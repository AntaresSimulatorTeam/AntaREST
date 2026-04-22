# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import re
from collections.abc import Callable
from datetime import timedelta
from functools import reduce
from pathlib import Path, PurePosixPath
from typing import cast
from uuid import uuid4

import humanize
from filelock import FileLock
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import (
    CommandNotFoundError,
    CommandNotValid,
    CommandUpdateAuthorizationError,
    NoParentStudyError,
    StudyNotFoundError,
    StudyValidationError,
    VariantGenerationError,
    VariantGenerationTimeoutError,
    VariantStudyParentNotValid,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde.json import to_json_string
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskResult, TaskType
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskNotifier, ITaskService, TaskNotFoundError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this, current_time, suppress_exception
from antarest.login.utils import get_user_id, get_user_impersonator, require_current_user
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.model import (
    StorageMode,
    Study,
    StudyMetadataDTO,
)
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.storage.abstract.abstract_service import AbstractService
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.file_study_storage import FileStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import (
    assert_permission,
    export_study_to_flat_directory,
    get_current_user_name,
    get_user_name_from_id,
    is_managed,
)
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.command_blob_usage_provider import CommandBlobUsageProvider
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.command_matrix_usage_provider import CommandMatrixUsageProvider
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    CommandDTOAPI,
    VariantTreeDTO,
)
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator

logger = logging.getLogger(__name__)


def _cast_study_to_variant(study: Study) -> VariantStudy:
    if not isinstance(study, VariantStudy):
        raise TypeError(f"The type of the study must be {VariantStudy}, not {type(study)}")
    return study


class VariantStudyService(AbstractService):
    def __init__(
        self,
        task_service: ITaskService,
        cache: ICache,
        raw_study_service: RawStudyService,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        repository: VariantStudyRepository,
        event_bus: IEventBus,
        config: Config,
        matrix_service: ISimpleMatrixService,
    ):
        super().__init__(cache, config)
        self.cache = cache
        self.config = config
        self.task_service = task_service
        self.raw_study_service = raw_study_service
        self.repository = repository
        self.event_bus = event_bus
        self.command_factory = command_factory
        self.study_factory = study_factory
        self._matrix_service = matrix_service
        ctx = command_factory.command_context
        self._storage_mapping: dict[StorageMode, IStudyStorage] = {
            StorageMode.FILESYSTEM: FileStudyStorage(cache, config, ctx, study_factory),
            StorageMode.DATABASE: DatabaseStudyStorage(
                config=config, matrix_service=matrix_service, generator_matrix_constants=ctx.generator_matrix_constants
            ),
        }
        CommandMatrixUsageProvider(variant_study_repo=repository, command_factory=command_factory)
        CommandBlobUsageProvider(variant_study_repo=repository, command_factory=command_factory)

    @override
    def copy(self, src_study: Study, dest_name: str, groups: list[str], destination_folder: PurePosixPath) -> Study:
        return self._storage_mapping[src_study.storage_mode].copy(src_study, dest_name, groups, destination_folder)

    @override
    def get_study_dao(self, study: Study) -> StudyDao:
        return self._storage_mapping[study.storage_mode].get_dao(study)

    @override
    def export_study_flat(self, study: Study, dst_path: Path) -> None:
        variant = _cast_study_to_variant(study)
        self.safe_generation(variant)
        export_study_to_flat_directory(variant.snapshot_dir, dst_path)

    ##########################
    # Specific methods
    ##########################

    def invalidate_snapshot(self, variant_study: VariantStudy) -> None:
        """
        Invalidates snapshot so that it is regenerated from scratch
        next time the study is accessed.
        """
        if variant_study.snapshot:
            variant_study.snapshot.last_executed_command = None
        variant_study.updated_at = current_time()
        self.repository.save(metadata=variant_study)

    def clear_snapshot(self, variant_study: VariantStudy) -> None:
        self._storage_mapping[variant_study.storage_mode].clear_snapshot(variant_study)
        self.invalidate_snapshot(variant_study)

    def _update_editor(self, study: VariantStudy) -> None:
        user_name = get_current_user_name()
        study.editor = user_name
        self.repository.save(study)

    def get_command(self, study_id: str, command_id: str) -> CommandDTOAPI:
        """
        Get command lists
        Args:
            study_id: study id
            command_id: command id
        Returns: List of commands
        """
        study = self._get_variant_study(study_id)

        try:
            index = [command.id for command in study.commands].index(command_id)
            command: CommandBlock = study.commands[index]
            user_name = get_user_name_from_id(command.user_id) if command.user_id else None
            return command.to_dto().to_api(user_name)
        except ValueError:
            raise CommandNotFoundError(f"Command with id {command_id} not found") from None

    def get_commands(self, study_id: str) -> list[CommandDTOAPI]:
        """
        Get commands list
        Args:
            study_id: study id
        Returns: List of commands
        """
        study = self._get_variant_study(study_id)

        id_to_name: dict[int, str] = {}
        command_list = []

        for command in study.commands:
            if command.user_id and command.user_id not in id_to_name.keys():
                user_name: str = get_user_name_from_id(command.user_id)
                id_to_name[command.user_id] = user_name
            command_list.append(command.to_dto().to_api(id_to_name.get(command.user_id)))
        return command_list

    def convert_commands(self, study_id: str, api_commands: list[CommandDTOAPI]) -> list[CommandDTO]:
        study = self._get_study_by_id(study_id)
        return [
            CommandDTO.model_validate({"study_version": study.version, **command.model_dump(mode="json")})
            for command in api_commands
        ]

    def _check_commands_validity(self, study_id: str, commands: list[CommandDTO]) -> list[ICommand]:
        command_objects: list[ICommand] = []
        for i, command in enumerate(commands):
            try:
                command_objects.extend(self.command_factory.to_command(command))
            except Exception as e:
                logger.error(f"Command at index {i} for study {study_id}", exc_info=e)
                raise CommandNotValid(f"Command at index {i} for study {study_id}") from None
        return command_objects

    def _check_update_authorization(self, metadata: VariantStudy) -> None:
        if metadata.generation_task:
            try:
                previous_task = self.task_service.status_task(metadata.generation_task)
                if not previous_task.status.is_final():
                    logger.error(f"{metadata.id} generation in progress")
                    raise CommandUpdateAuthorizationError(metadata.id)
            except TaskNotFoundError as e:
                logger.warning(
                    f"Failed to retrieve generation task for study {metadata.id}",
                    exc_info=e,
                )

    def append_command(self, study_id: str, command: CommandDTO) -> str:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            command: new command
        Returns: None
        """
        command_ids = self.append_commands(study_id, [command])
        return command_ids[0]

    def append_commands(self, study_id: str, commands: list[CommandDTO]) -> list[str]:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            commands: list of new command
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, commands)
        validated_commands = transform_command_to_dto(command_objs, commands)
        first_index = len(study.commands)

        # noinspection PyArgumentList
        new_commands = [
            CommandBlock(
                command=command.action,
                args=to_json_string(command.args),
                index=(first_index + i),
                version=command.version,
                study_version=str(command.study_version),
                user_id=get_user_impersonator(),
                updated_at=current_time(),
            )
            for i, command in enumerate(validated_commands)
        ]
        study.commands.extend(new_commands)
        self._update_editor(study)
        self.on_variant_advance(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return [c.id for c in new_commands]

    def replace_commands(self, study_id: str, commands: list[CommandDTO]) -> str:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            commands: list of new command
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, commands)
        validated_commands = transform_command_to_dto(command_objs, commands)
        # noinspection PyArgumentList
        study.commands = [
            CommandBlock(
                command=command.action,
                args=to_json_string(command.args),
                index=i,
                version=command.version,
                study_version=str(command.study_version),
                user_id=get_user_id(),
                updated_at=current_time(),
            )
            for i, command in enumerate(validated_commands)
        ]
        self._update_editor(study)
        self.on_variant_rebase(study)
        return str(study.id)

    def move_command(self, study_id: str, command_id: str, new_index: int) -> None:
        """
        Move command place in the list of command
        Args:
            study_id: study id
            command_id: command_id
            new_index: new index of the command
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)

        index = [command.id for command in study.commands].index(command_id)
        if index >= 0 and len(study.commands) > new_index >= 0:
            command = study.commands[index]
            study.commands.pop(index)
            study.commands.insert(new_index, command)
            for idx in range(len(study.commands)):
                study.commands[idx].index = idx
            self._update_editor(study)
            self.on_variant_rebase(study)

    def remove_command(self, study_id: str, command_id: str) -> None:
        """
        Remove command
        Args:
            study_id: study id
            command_id: command_id
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)

        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands.pop(index)
            for idx, command in enumerate(study.commands):
                command.index = idx
            self._update_editor(study)
            self.on_variant_rebase(study)

    def remove_all_commands(self, study_id: str) -> None:
        """
        Remove all commands
        Args:
            study_id: study id
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)

        study.commands = []
        self._update_editor(study)
        self.on_variant_rebase(study)

    def update_command(self, study_id: str, command_id: str, command: CommandDTO) -> None:
        """
        Update a command
        Args:
            study_id: study id
            command_id: command id
            command: new command
        Returns: None
        """
        study = self._get_variant_study(study_id)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, [command])
        validated_commands = transform_command_to_dto(command_objs, [command])
        assert_this(len(validated_commands) == 1)
        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands[index].command = validated_commands[0].action
            study.commands[index].args = to_json_string(validated_commands[0].args)
            self._update_editor(study)
            self.on_variant_rebase(study)

    def export_commands_matrices(self, study_id: str) -> FileDownloadTaskDTO:
        study = self._get_variant_study(study_id)
        matrices = {
            matrix
            for command in study.commands
            for matrix in suppress_exception(
                lambda: reduce(
                    lambda m, c: m + c.get_inner_matrices().matrices,
                    self.command_factory.to_command(command.to_dto()),
                    cast(list[str], []),
                ),
                lambda e: logger.warning(f"Failed to parse command {command}", exc_info=e),
            )
            or []
        }
        matrix_service = cast(MatrixService, self._matrix_service)
        return matrix_service.download_matrix_list(list(matrices), f"{study.name}_{study.id}_matrices")

    def _get_variant_study(
        self,
        study_id: str,
    ) -> VariantStudy:
        """
        Get variant study, and check READ permissions.

        Args:
            study_id: The study identifier.

        Returns:
            The variant study.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
        """
        study = self._get_study_by_id(study_id)

        assert isinstance(study, VariantStudy)
        return study

    def _get_study_by_id(
        self,
        study_id: str,
    ) -> Study:
        """
        Get study, and check READ permissions.

        Args:
            study_id: The study identifier.

        Returns:
            The variant study.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
        """
        study = self.repository.get(study_id)

        if study is None:
            raise StudyNotFoundError(study_id)

        assert_permission(study, StudyPermissionType.READ)
        return study

    def on_variant_advance(self, study: VariantStudy) -> None:
        """
        Takes necessary actions when some study commands have been appended to this study.
        It will need a snapshot generation (NOT from scratch),
        and children need to be notified of their parent change.
        """
        study.updated_at = current_time()
        self.repository.save(metadata=study)
        self.on_parent_change(study.id)

    def get_children(self, parent_id: str) -> list[VariantStudy]:
        """
        Get the direct children of the specified study (in chronological creation order).
        """
        return self.repository.get_children(parent_id=parent_id)

    def on_variant_rebase(self, study: VariantStudy) -> None:
        """
        This variant has been "rebased" in the sense of git (history changed):
        it will need a generation from scratch, and children need
        to be rebased too.
        """
        self.invalidate_snapshot(study)
        self.on_parent_change(study.id)

    def on_parent_change(self, study_id: str) -> None:
        """
        Takes all necessary actions on children when a study history has changed.
        """
        # TODO: optimize to not perform one request per child
        for child in self.get_children(parent_id=study_id):
            self.on_variant_rebase(child)

    def has_children(self, study: Study) -> bool:
        return self.repository.has_children(study.id)

    def get_all_variants_children(self, parent_id: str) -> VariantTreeDTO:
        study = self._get_study_by_id(parent_id)
        children_tree = VariantTreeDTO(
            node=self.get_study_information(study),
            children=[],
        )
        children = self.get_children(parent_id=parent_id)
        for child in children:
            try:
                children_tree.children.append(self.get_all_variants_children(child.id))
            except UserHasNotPermissionError:
                logger.info(
                    f"Filtering children {child.id} in variant tree since user has not permission on this study"
                )

        return children_tree

    def walk_children(
        self,
        parent_id: str,
        fun: Callable[[Study], None],
        bottom_first: bool,
        include_parent: bool = True,
    ) -> None:
        study = self._get_study_by_id(parent_id)
        children = self.get_children(parent_id=parent_id)
        # TODO : the bottom_first should always be True, otherwise we will have an infinite loop
        if include_parent and not bottom_first:
            fun(study)
        for child in children:
            self.walk_children(child.id, fun, bottom_first)
        if include_parent and bottom_first:
            fun(study)

    def get_variants_parents(self, study_id: str) -> list[StudyMetadataDTO]:
        output_list: list[StudyMetadataDTO] = self._get_variants_parents(study_id)
        if output_list:
            output_list = output_list[1:]
        return output_list

    def get_direct_parent(self, id: str) -> StudyMetadataDTO | None:
        study = self._get_study_by_id(id)
        if study.parent_id is not None:
            parent = self._get_study_by_id(study.parent_id)
            return (
                self.get_study_information(
                    parent,
                )
                if isinstance(parent, VariantStudy)
                else self.raw_study_service.get_study_information(
                    parent,
                )
            )
        return None

    def _get_variants_parents(self, id: str) -> list[StudyMetadataDTO]:
        study = self._get_study_by_id(id)
        metadata = (
            self.get_study_information(
                study,
            )
            if isinstance(study, VariantStudy)
            else self.raw_study_service.get_study_information(
                study,
            )
        )
        output_list: list[StudyMetadataDTO] = [metadata]
        if study.parent_id is not None:
            output_list.extend(self._get_variants_parents(study.parent_id))

        return output_list

    def create_variant_study(self, uuid: str, name: str) -> VariantStudy:
        """
        Create a new variant study.

        Args:
            uuid: The UUID of the parent study.
            name: The name of the new variant study.

        Returns:
            The newly created variant study.

        Raises:
            StudyNotFoundError:
                If the parent study with the given UUID does not exist.
            VariantStudyParentNotValid:
                If the parent study is not managed and cannot be used to create a variant.
        """
        study = self.repository.get(uuid)

        if study is None:
            raise StudyNotFoundError(uuid)

        if not is_managed(study):
            raise VariantStudyParentNotValid(
                f"The study {study.name} is not managed. Cannot create a variant from it. It must be imported first."
            )

        assert_permission(study, StudyPermissionType.READ)
        new_id = str(uuid4())
        study_path = str(self.config.get_workspace_path() / new_id)
        user_name = get_current_user_name()

        now_utc = current_time()
        variant_study = VariantStudy(
            id=new_id,
            name=name,
            parent_id=uuid,
            path=study_path,
            directory_id=study.directory_id,
            public_mode=study.public_mode,
            created_at=now_utc,
            updated_at=now_utc,
            version=study.version,
            author=study.author,
            editor=user_name,
            horizon=study.horizon,
            folder=(re.sub(study.id, new_id, study.folder) if study.folder is not None else None),
            groups=study.groups,  # Create inherit_group boolean
            owner_id=require_current_user().impersonator,
            snapshot=None,
        )
        self.repository.save(variant_study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=variant_study.to_json_summary(),
                permissions=PermissionInfo.from_study(variant_study),
            )
        )
        logger.info(
            "variant study %s created by user %s",
            variant_study.id,
            get_user_id(),
        )
        return variant_study

    def generate_task(
        self,
        metadata: VariantStudy,
        from_scratch: bool = False,
        listener: ICommandListener | None = None,
    ) -> str:
        study_id = metadata.id
        with FileLock(str(self.config.storage.tmp_dir / f"study-generation-{study_id}.lock")):
            logger.info(f"Starting variant study {study_id} generation")
            self.repository.refresh(metadata)
            if metadata.generation_task:
                try:
                    previous_task = self.task_service.status_task(metadata.generation_task)
                    if not previous_task.status.is_final():
                        logger.info(f"Returning already existing variant study {study_id} generation")
                        return str(metadata.generation_task)
                except TaskNotFoundError as e:
                    logger.warning(
                        f"Failed to retrieve generation task for study {study_id}",
                        exc_info=e,
                    )

            # this is important because the callback will be called outside the current
            # db context, so we need to fetch the id attribute before
            study_id = metadata.id

            def callback(notifier: ITaskNotifier) -> TaskResult:
                generator = SnapshotGenerator(variant_study_service=self)

                # Build the Dao factory first
                ctx = self.command_factory.command_context
                factory: StudyFactoryDao
                if metadata.storage_mode == StorageMode.FILESYSTEM:
                    factory = FileStudyDaoFactory(ctx, self.study_factory, self.cache)
                else:
                    factory = DatabaseStudyDaoFactory(ctx.matrix_service, ctx.generator_matrix_constants)
                # Then launch the generation
                generate_result = generator.generate_snapshot(
                    study_id,
                    dao_factory=factory,
                    from_scratch=from_scratch,
                    notifier=notifier,
                    listener=listener,
                )
                return TaskResult(
                    success=generate_result.success,
                    message=(
                        f"{study_id} generated successfully" if generate_result.success else f"{study_id} not generated"
                    ),
                    return_value=generate_result.model_dump_json(),
                )

            metadata.generation_task = self.task_service.add_task(
                action=callback,
                name=f"Generation of {metadata.id} study",
                task_type=TaskType.VARIANT_GENERATION,
                ref_id=study_id,
                progress=None,
                custom_event_messages=CustomTaskEventMessages(start=metadata.id, running=metadata.id, end=metadata.id),
            )
            self.repository.save(metadata)
            return str(metadata.generation_task)

    def generate(self, variant_study_id: str, from_scratch: bool) -> str:
        # Get variant study
        variant_study = self._get_variant_study(variant_study_id)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        return self.generate_task(variant_study, from_scratch=from_scratch)

    def get_study_task(self, study_id: str) -> TaskDTO:
        """
        Get the generation task ID of a variant study.

        Args:
            study_id: The ID of the variant study.

        Returns:
            The generation task ID.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
            StudyTypeUnsupported: If the study is not a variant study (HTTP status 422).
            StudyValidationError: If the study has no generation task (HTTP status 422).
        """
        variant_study = self._get_variant_study(study_id)
        task_id = variant_study.generation_task
        if task_id:
            return self.task_service.status_task(task_id=task_id, with_logs=True)
        raise StudyValidationError(f"Variant study '{study_id}' has no generation task")

    def create_snapshot(self, ref_study: Study, variant_study: VariantStudy) -> None:
        self._storage_mapping[ref_study.storage_mode].create_snapshot(ref_study, variant_study)

    def clear_all_snapshots(self, retention_time: timedelta) -> str:
        """
        Admin command that clear all variant snapshots older than `retention_hours` (in hours).
        Only available for admin users.

        Args:
            retention_time: number of retention hours
        Returns: None

        Raises:
            UserHasNotPermissionError
        """
        user = require_current_user()
        if not (user.is_site_admin() or user.is_admin_token()):
            raise UserHasNotPermissionError()

        task_name = f"Cleaning all snapshot updated or accessed at least {humanize.precisedelta(retention_time)} ago."

        snapshot_clearing_task_instance = SnapshotCleanerTask(variant_study_service=self, retention_time=retention_time)

        return self.task_service.add_task(
            snapshot_clearing_task_instance,
            task_name,
            task_type=TaskType.SNAPSHOT_CLEARING,
            ref_id=None,
            progress=None,
            custom_event_messages=None,
        )

    def safe_generation(self, study: VariantStudy, timeout: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        try:
            if self._storage_mapping[study.storage_mode].is_snapshot_up_to_date(study):
                # Nothing to do
                return

            logger.info("🔹 Starting variant study generation...")
            # Create and run the generation task in a thread pool.
            task_id = self.generate_task(study)
            self.task_service.await_task(task_id, timeout)
            result = self.task_service.status_task(task_id)
            if not result.result:
                raise ValueError("No task result")
            if result.result.success:
                # OK, the study has been generated
                return
            # The variant generation failed, we have to raise a clear exception.
            error_msg = result.result.message
            stripped_msg = error_msg.removeprefix(f"417: Failed to generate variant study {study.id}")
            raise ValueError(stripped_msg)

        except TimeoutError as e:
            # Raise a REQUEST_TIMEOUT error (408)
            msg = f"⚡ Timeout while waiting for generation of variant study {study.id}"
            logger.error(msg, exc_info=e)
            raise VariantGenerationTimeoutError(msg) from None

        except Exception as e:
            # raise a EXPECTATION_FAILED error (417)
            logger.error(f"⚡ Fail to generate variant study {study.id}", exc_info=e)
            raise VariantGenerationError(f"Error while generating variant {study.id} {e}") from None


class SnapshotCleanerTask:
    def __init__(
        self,
        variant_study_service: VariantStudyService,
        retention_time: timedelta,
    ) -> None:
        self._variant_study_service = variant_study_service
        self._retention_time = retention_time

    def _clear_all_snapshots(self) -> None:
        with db():
            variant_list = self._variant_study_service.repository.get_all(
                study_filter=StudyFilter(
                    variant=True,
                    access_permissions=AccessPermissions(is_admin=True),
                )
            )
            for variant in variant_list:
                assert isinstance(variant, VariantStudy)
                now_utc = current_time()
                if variant.updated_at and variant.updated_at < now_utc - self._retention_time:
                    if variant.last_access and variant.last_access < now_utc - self._retention_time:
                        self._variant_study_service.clear_snapshot(variant)

    def run_task(self, notifier: ITaskNotifier) -> TaskResult:
        msg = f"Start cleaning all snapshots updated or accessed {humanize.precisedelta(self._retention_time)} ago."
        notifier.notify_message(msg)
        self._clear_all_snapshots()
        msg = "All selected snapshots were successfully cleared."
        notifier.notify_message(msg)
        return TaskResult(success=True, message=msg)

    __call__ = run_task
