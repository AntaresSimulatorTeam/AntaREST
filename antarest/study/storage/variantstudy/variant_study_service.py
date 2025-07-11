# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import concurrent.futures
import logging
import re
import shutil
import typing as t
from datetime import datetime, timedelta
from functools import reduce
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, List, Optional, Sequence, cast
from uuid import uuid4

import humanize
from fastapi import HTTPException
from filelock import FileLock
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import (
    CommandNotFoundError,
    CommandNotValid,
    CommandUpdateAuthorizationError,
    NoParentStudyError,
    StudyNotFoundError,
    StudyTypeUnsupported,
    StudyValidationError,
    VariantGenerationError,
    VariantGenerationTimeoutError,
    VariantStudyParentNotValid,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import JSON, PermissionInfo, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde.json import to_json_string
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskResult, TaskType
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskNotifier, ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this, suppress_exception
from antarest.login.model import Identity
from antarest.login.utils import get_user_id, require_current_user
from antarest.matrixstore.service import MatrixService
from antarest.study.model import (
    RawStudy,
    Study,
    StudyAdditionalData,
    StudyMetadataDTO,
    StudySimResultDTO,
)
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService, copy_output_folders
from antarest.study.storage.utils import (
    assert_permission,
    export_study_flat,
    is_managed,
    remove_from_cache,
    update_antares_info,
)
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.command_factory import CommandFactory
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
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator

logger = logging.getLogger(__name__)

SNAPSHOT_RELATIVE_PATH = "snapshot"
OUTPUT_RELATIVE_PATH = "output"


class VariantStudyService(AbstractStorageService):
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
    ):
        super().__init__(
            config=config,
            study_factory=study_factory,
            cache=cache,
        )
        self.task_service = task_service
        self.raw_study_service = raw_study_service
        self.repository = repository
        self.event_bus = event_bus
        self.command_factory = command_factory
        self.generator = VariantCommandGenerator(self.study_factory)

    @staticmethod
    def _get_user_name_from_id(user_id: int) -> str:
        """
        Utility method that retrieves a user's name based on their id.
        Args:
            user_id: user id (user must exist)
        Returns: String representing the user's name
        """
        user_obj: Identity | None = db.session.get(Identity, user_id)
        if user_obj is None:
            raise ValueError(f"User with id {user_id} not found")
        return str(user_obj.name)

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
            user_name = self._get_user_name_from_id(command.user_id) if command.user_id else None
            return command.to_dto().to_api(user_name)
        except ValueError:
            raise CommandNotFoundError(f"Command with id {command_id} not found") from None

    def get_commands(self, study_id: str) -> List[CommandDTOAPI]:
        """
        Get commands list
        Args:
            study_id: study id
        Returns: List of commands
        """
        study = self._get_variant_study(study_id)

        id_to_name: Dict[int, str] = {}
        command_list = []

        for command in study.commands:
            if command.user_id and command.user_id not in id_to_name.keys():
                user_name: str = self._get_user_name_from_id(command.user_id)
                id_to_name[command.user_id] = user_name
            command_list.append(command.to_dto().to_api(id_to_name.get(command.user_id)))
        return command_list

    def convert_commands(self, study_id: str, api_commands: List[CommandDTOAPI]) -> List[CommandDTO]:
        study = self._get_variant_study(study_id, raw_study_accepted=True)
        return [
            CommandDTO.model_validate({"study_version": study.version, **command.model_dump(mode="json")})
            for command in api_commands
        ]

    def _check_commands_validity(self, study_id: str, commands: List[CommandDTO]) -> List[ICommand]:
        command_objects: List[ICommand] = []
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
            except HTTPException as e:
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

    def append_commands(self, study_id: str, commands: List[CommandDTO]) -> List[str]:
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
                user_id=get_user_id(),
                updated_at=datetime.utcnow(),
            )
            for i, command in enumerate(validated_commands)
        ]
        study.commands.extend(new_commands)
        self.on_variant_advance(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return [c.id for c in new_commands]

    def replace_commands(self, study_id: str, commands: List[CommandDTO]) -> str:
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
                updated_at=datetime.utcnow(),
            )
            for i, command in enumerate(validated_commands)
        ]
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
            self.on_variant_rebase(study)

    def export_commands_matrices(self, study_id: str) -> FileDownloadTaskDTO:
        study = self._get_variant_study(study_id)
        matrices = {
            matrix
            for command in study.commands
            for matrix in suppress_exception(
                lambda: reduce(
                    lambda m, c: m + c.get_inner_matrices(),
                    self.command_factory.to_command(command.to_dto()),
                    cast(List[str], []),
                ),
                lambda e: logger.warning(f"Failed to parse command {command}", exc_info=e),
            )
            or []
        }
        return cast(MatrixService, self.command_factory.command_context.matrix_service).download_matrix_list(
            list(matrices), f"{study.name}_{study.id}_matrices"
        )

    def _get_variant_study(
        self,
        study_id: str,
        raw_study_accepted: bool = False,
    ) -> VariantStudy:
        """
        Get variant study (or RAW study if `raw_study_accepted` is `True`), and check READ permissions.

        Args:
            study_id: The study identifier.

        Returns:
            The variant study.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
            StudyTypeUnsupported: If the study is not a variant study (HTTP status 422).
        """
        study = self.repository.get(study_id)

        if study is None:
            raise StudyNotFoundError(study_id)

        if not isinstance(study, VariantStudy) and not raw_study_accepted:
            raise StudyTypeUnsupported(study_id, study.type)

        assert_permission(study, StudyPermissionType.READ)
        return study

    def on_variant_advance(self, study: VariantStudy) -> None:
        """
        Takes necessary actions when some study commands have been appended to this study.
        It will need a snapshot generation (NOT from scratch),
        and children need to be notified of their parent change.
        """
        self.repository.save(
            metadata=study,
            update_modification_date=True,
        )
        self.on_parent_change(study.id)

    def get_children(self, parent_id: str) -> List[VariantStudy]:
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
        self._invalidate_snapshot(study)
        self.on_parent_change(study.id)

    def on_parent_change(self, study_id: str) -> None:
        """
        Takes all necessary actions on children when a study history has changed.
        """
        # TODO: optimize to not perform one request per child
        for child in self.get_children(parent_id=study_id):
            self.on_variant_rebase(child)

    def _invalidate_snapshot(
        self,
        variant_study: VariantStudy,
    ) -> None:
        """
        Invalidates snapshot so that it is regenerated from scratch
        next time the study is accessed.
        """
        if variant_study.snapshot:
            variant_study.snapshot.last_executed_command = None
        self.repository.save(
            metadata=variant_study,
            update_modification_date=True,
        )

    def clear_snapshot(self, variant_study: Study) -> None:
        logger.info(f"Clearing snapshot for study {variant_study.id}")
        self._invalidate_snapshot(variant_study)
        shutil.rmtree(self.get_study_path(variant_study), ignore_errors=True)

    def has_children(self, study: VariantStudy) -> bool:
        return self.repository.has_children(study.id)

    def get_all_variants_children(self, parent_id: str) -> VariantTreeDTO:
        study = self._get_variant_study(parent_id, raw_study_accepted=True)

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
        fun: Callable[[VariantStudy], None],
        bottom_first: bool,
    ) -> None:
        study = self._get_variant_study(
            parent_id,
            raw_study_accepted=True,
        )
        children = self.get_children(parent_id=parent_id)
        # TODO : the bottom_first should always be True, otherwise we will have an infinite loop
        if not bottom_first:
            fun(study)
        for child in children:
            self.walk_children(child.id, fun, bottom_first)
        if bottom_first:
            fun(study)

    def get_variants_parents(self, study_id: str) -> List[StudyMetadataDTO]:
        output_list: List[StudyMetadataDTO] = self._get_variants_parents(study_id)
        if output_list:
            output_list = output_list[1:]
        return output_list

    def get_direct_parent(self, id: str) -> Optional[StudyMetadataDTO]:
        study = self._get_variant_study(id, raw_study_accepted=True)
        if study.parent_id is not None:
            parent = self._get_variant_study(study.parent_id, raw_study_accepted=True)
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

    def _get_variants_parents(self, id: str) -> List[StudyMetadataDTO]:
        study = self._get_variant_study(id, raw_study_accepted=True)
        metadata = (
            self.get_study_information(
                study,
            )
            if isinstance(study, VariantStudy)
            else self.raw_study_service.get_study_information(
                study,
            )
        )
        output_list: List[StudyMetadataDTO] = [metadata]
        if study.parent_id is not None:
            output_list.extend(self._get_variants_parents(study.parent_id))

        return output_list

    @override
    def get(
        self,
        metadata: VariantStudy,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
        use_cache: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted
            use_cache: indicate if cache should be used

        Returns: study data formatted in json
        """
        self._safe_generation(metadata, timeout=600)
        self.repository.refresh(metadata)
        return super().get(
            metadata=metadata,
            url=url,
            depth=depth,
            formatted=formatted,
            use_cache=use_cache,
        )

    @override
    def get_file(
        self,
        metadata: VariantStudy,
        url: str = "",
        use_cache: bool = True,
    ) -> OriginalFile:
        """
        Entry point to fetch for a file inside a study folder.
        Args:
            metadata: study
            url: path data inside study to reach
            use_cache: indicate if cache should be used to fetch study tree

        Returns: the file content and extension
        """
        self._safe_generation(metadata, timeout=600)
        self.repository.refresh(metadata)
        return super().get_file(
            metadata=metadata,
            url=url,
            use_cache=use_cache,
        )

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
        if study.additional_data is None:
            additional_data = StudyAdditionalData()
        else:
            additional_data = StudyAdditionalData(
                horizon=study.additional_data.horizon,
                author=study.additional_data.author,
                patch=study.additional_data.patch,
            )

        variant_study = VariantStudy(
            id=new_id,
            name=name,
            parent_id=uuid,
            path=study_path,
            public_mode=study.public_mode,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=study.version,
            folder=(re.sub(study.id, new_id, study.folder) if study.folder is not None else None),
            groups=study.groups,  # Create inherit_group boolean
            owner_id=require_current_user().impersonator,
            snapshot=None,
            additional_data=additional_data,
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
        denormalize: bool = False,
        from_scratch: bool = False,
        listener: Optional[ICommandListener] = None,
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
                except HTTPException as e:
                    logger.warning(
                        f"Failed to retrieve generation task for study {study_id}",
                        exc_info=e,
                    )

            # this is important because the callback will be called outside the current
            # db context, so we need to fetch the id attribute before
            study_id = metadata.id

            def callback(notifier: ITaskNotifier) -> TaskResult:
                generator = SnapshotGenerator(
                    cache=self.cache,
                    raw_study_service=self.raw_study_service,
                    command_factory=self.command_factory,
                    study_factory=self.study_factory,
                    repository=self.repository,
                )
                generate_result = generator.generate_snapshot(
                    study_id,
                    denormalize=denormalize,
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

    def generate(self, variant_study_id: str, denormalize: bool, from_scratch: bool) -> str:
        # Get variant study
        variant_study = self._get_variant_study(variant_study_id)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        return self.generate_task(variant_study, denormalize, from_scratch=from_scratch)

    def _to_commands(self, metadata: VariantStudy, from_index: int = 0) -> t.List[t.List[ICommand]]:
        commands: List[List[ICommand]] = [
            self.command_factory.to_command(command_block.to_dto())
            for index, command_block in enumerate(metadata.commands)
            if from_index <= index
        ]
        return commands

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

    @override
    def create(self, study: VariantStudy) -> VariantStudy:
        """
        Create an empty new study.
        Args:
            study: Study information.
        Returns: New study information.
        """
        raise NotImplementedError()

    @override
    def exists(self, metadata: VariantStudy) -> bool:
        """
        Check if the study snapshot exists and is up-to-date.

        Args:
            metadata: Study metadata.

        Returns: `True` if the study is present on disk, `False` otherwise.
        """
        return (
            (metadata.snapshot is not None)
            and (metadata.snapshot.created_at >= metadata.updated_at)
            and (self.get_study_path(metadata) / "study.antares").is_file()
        )

    @override
    def copy(
        self,
        src_study: VariantStudy,
        dest_study_name: str,
        groups: Sequence[str],
        destination_folder: PurePosixPath,
        output_ids: List[str],
        with_outputs: bool | None,
    ) -> RawStudy:
        """
        Create a new variant study by copying a reference study.

        Args:
            src_study: The source study that you want to copy.
            dest_study_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            destination_folder: Path where the destination study will be stored. If not specified, the destination path will be the same as the source study.
            output_ids: A list of output names that you want to include in the destination study.
            with_outputs: Indicates whether to copy the outputs as well.

        Returns:
            The newly created study.
        """

        dest_study = self.raw_study_service.build_raw_study(dest_study_name, groups, src_study, destination_folder)

        file_study = self.get_raw(metadata=src_study)

        src_path = file_study.config.path
        dest_path = dest_study.path
        shutil.copytree(src_path, dest_path)

        src_path = cast(Path, file_study.config.output_path)
        if src_path.exists():
            dest_output_path = Path(dest_study.path) / OUTPUT_RELATIVE_PATH
            copy_output_folders(src_path, dest_output_path, with_outputs, output_ids)

        update_antares_info(dest_study, file_study.tree, update_author=True)
        return dest_study

    def _safe_generation(self, metadata: VariantStudy, timeout: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        try:
            if self.exists(metadata):
                # The study is already present on disk => nothing to do
                return

            logger.info("🔹 Starting variant study generation...")
            # Create and run the generation task in a thread pool.
            task_id = self.generate_task(metadata)
            self.task_service.await_task(task_id, timeout)
            result = self.task_service.status_task(task_id)
            if not result.result:
                raise ValueError("No task result")
            if result.result.success:
                # OK, the study has been generated
                return
            # The variant generation failed, we have to raise a clear exception.
            error_msg = result.result.message
            stripped_msg = error_msg.removeprefix(f"417: Failed to generate variant study {metadata.id}")
            raise ValueError(stripped_msg)

        except concurrent.futures.TimeoutError as e:
            # Raise a REQUEST_TIMEOUT error (408)
            logger.error(f"⚡ Timeout while generating variant study {metadata.id}", exc_info=e)
            raise VariantGenerationTimeoutError(f"Timeout while generating variant {metadata.id}") from None

        except Exception as e:
            # raise a EXPECTATION_FAILED error (417)
            logger.error(f"⚡ Fail to generate variant study {metadata.id}", exc_info=e)
            raise VariantGenerationError(f"Error while generating variant {metadata.id} {e}") from None

    @staticmethod
    def _get_snapshot_last_executed_command_index(
        study: VariantStudy,
    ) -> Optional[int]:
        if study.snapshot and study.snapshot.last_executed_command:
            last_executed_command_index = [command.id for command in study.commands].index(
                study.snapshot.last_executed_command
            )
            return last_executed_command_index if last_executed_command_index >= 0 else None
        return None

    @override
    def get_raw(
        self,
        metadata: VariantStudy,
        use_cache: bool = True,
        output_dir: Optional[Path] = None,
    ) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object
        """
        self._safe_generation(metadata)

        study_path = self.get_study_path(metadata)
        return self.study_factory.create_from_fs(
            study_path,
            is_managed(metadata),
            metadata.id,
            output_dir or Path(metadata.path) / "output",
            use_cache=use_cache,
        )

    @override
    def get_study_sim_result(self, study: VariantStudy) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        self._safe_generation(study, timeout=600)
        return super().get_study_sim_result(study=study)

    @override
    def delete(self, metadata: VariantStudy) -> None:
        """
        Delete study
        Args:
            metadata: study
        Returns:
        """
        study_path = Path(metadata.path)
        if study_path.exists():
            shutil.rmtree(study_path)
            remove_from_cache(self.cache, metadata.id)

    @override
    def delete_output(self, metadata: VariantStudy, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation
        Returns:
        """
        study_path = Path(metadata.path)
        output_path = study_path / "output" / output_id
        shutil.rmtree(output_path, ignore_errors=True)
        remove_from_cache(self.cache, metadata.id)

    @override
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        return Path(metadata.path) / SNAPSHOT_RELATIVE_PATH

    @override
    def export_study_flat(
        self,
        metadata: VariantStudy,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: Optional[List[str]] = None,
        denormalize: bool = True,
    ) -> None:
        self._safe_generation(metadata)
        path_study = Path(metadata.path)

        snapshot_path = path_study / SNAPSHOT_RELATIVE_PATH
        output_src_path = path_study / "output"
        export_study_flat(
            snapshot_path,
            dst_path,
            self.study_factory,
            outputs,
            output_list_filter,
            denormalize,
            output_src_path,
            is_managed(metadata),
        )

    @override
    def get_synthesis(self, metadata: VariantStudy) -> FileStudyTreeConfigDTO:
        """
        Return study synthesis
        Args:
            metadata: study
        Returns: FileStudyTreeConfigDTO

        """
        self._safe_generation(metadata)
        study_path = self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(study_path, is_managed(metadata), metadata.id)
        return FileStudyTreeConfigDTO.from_build_config(study.config)

    @override
    def initialize_additional_data(self, variant_study: VariantStudy) -> bool:
        try:
            if self.exists(variant_study):
                study = self.study_factory.create_from_fs(
                    self.get_study_path(variant_study),
                    is_managed(variant_study),
                    study_id=variant_study.id,
                    output_path=Path(variant_study.path) / OUTPUT_RELATIVE_PATH,
                )
                variant_study.additional_data = self._read_additional_data_from_files(study)
            else:
                variant_study.additional_data = StudyAdditionalData()
            return True
        except Exception as e:
            logger.error(
                f"Error while reading additional data for study {variant_study.id}",
                exc_info=e,
            )
            return False

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

    @override
    def get_output_path(self, study: Study, output_id: str) -> Path:
        return Path(study.path) / "output" / output_id


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
                if variant.updated_at and variant.updated_at < datetime.utcnow() - self._retention_time:
                    if variant.last_access and variant.last_access < datetime.utcnow() - self._retention_time:
                        self._variant_study_service.clear_snapshot(variant)

    def run_task(self, notifier: ITaskNotifier) -> TaskResult:
        msg = f"Start cleaning all snapshots updated or accessed {humanize.precisedelta(self._retention_time)} ago."
        notifier.notify_message(msg)
        self._clear_all_snapshots()
        msg = "All selected snapshots were successfully cleared."
        notifier.notify_message(msg)
        return TaskResult(success=True, message=msg)

    __call__ = run_task
