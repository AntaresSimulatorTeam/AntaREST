import concurrent.futures
import json
import logging
import re
import shutil
import typing as t
from datetime import datetime
from functools import reduce
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from filelock import FileLock

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
from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON, PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskResult, TaskType
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskService, TaskUpdateNotifier, noop_notifier
from antarest.core.utils.utils import assert_this, suppress_exception
from antarest.matrixstore.service import MatrixService
from antarest.study.model import RawStudy, Study, StudyAdditionalData, StudyMetadataDTO, StudySimResultDTO
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import assert_permission, export_study_flat, is_managed, remove_from_cache
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    CommandResultDTO,
    GenerationResultInfoDTO,
    VariantTreeDTO,
)
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator

logger = logging.getLogger(__name__)

SNAPSHOT_RELATIVE_PATH = "snapshot"
OUTPUT_RELATIVE_PATH = "output"


class VariantStudyService(AbstractStorageService[VariantStudy]):
    def __init__(
        self,
        task_service: ITaskService,
        cache: ICache,
        raw_study_service: RawStudyService,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        patch_service: PatchService,
        repository: VariantStudyRepository,
        event_bus: IEventBus,
        config: Config,
    ):
        super().__init__(
            config=config,
            study_factory=study_factory,
            patch_service=patch_service,
            cache=cache,
        )
        self.task_service = task_service
        self.raw_study_service = raw_study_service
        self.repository = repository
        self.event_bus = event_bus
        self.command_factory = command_factory
        self.generator = VariantCommandGenerator(self.study_factory)

    def get_command(self, study_id: str, command_id: str, params: RequestParameters) -> CommandDTO:
        """
        Get command lists
        Args:
            study_id: study id
            command_id: command id
            params: request parameters
        Returns: List of commands
        """
        study = self._get_variant_study(study_id, params)

        try:
            index = [command.id for command in study.commands].index(command_id)  # Maybe add Try catch for this
            return t.cast(CommandDTO, study.commands[index].to_dto())
        except ValueError:
            raise CommandNotFoundError(f"Command with id {command_id} not found") from None

    def get_commands(self, study_id: str, params: RequestParameters) -> t.List[CommandDTO]:
        """
        Get command lists
        Args:
            study_id: study id
            params: request parameters
        Returns: List of commands
        """
        study = self._get_variant_study(study_id, params)
        return [command.to_dto() for command in study.commands]

    def _check_commands_validity(self, study_id: str, commands: t.List[CommandDTO]) -> t.List[ICommand]:
        command_objects: t.List[ICommand] = []
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
                previous_task = self.task_service.status_task(
                    metadata.generation_task,
                    RequestParameters(DEFAULT_ADMIN_USER),
                )
                if not previous_task.status.is_final():
                    logger.error(f"{metadata.id} generation in progress")
                    raise CommandUpdateAuthorizationError(metadata.id)
            except HTTPException as e:
                logger.warning(
                    f"Failed to retrieve generation task for study {metadata.id}",
                    exc_info=e,
                )

    def append_command(self, study_id: str, command: CommandDTO, params: RequestParameters) -> str:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            command: new command
            params: request parameters
        Returns: None
        """
        command_ids = self.append_commands(study_id, [command], params)
        return command_ids[0]

    def append_commands(
        self,
        study_id: str,
        commands: t.List[CommandDTO],
        params: RequestParameters,
    ) -> t.List[str]:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            commands: list of new command
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, commands)
        validated_commands = transform_command_to_dto(command_objs, commands)
        first_index = len(study.commands)
        # noinspection PyArgumentList
        new_commands = [
            CommandBlock(
                command=command.action, args=json.dumps(command.args), index=(first_index + i), version=command.version
            )
            for i, command in enumerate(validated_commands)
        ]
        study.commands.extend(new_commands)
        self.invalidate_cache(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return [c.id for c in new_commands]

    def replace_commands(
        self,
        study_id: str,
        commands: t.List[CommandDTO],
        params: RequestParameters,
    ) -> str:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            commands: list of new command
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, commands)
        validated_commands = transform_command_to_dto(command_objs, commands)
        # noinspection PyArgumentList
        study.commands = [
            CommandBlock(command=command.action, args=json.dumps(command.args), index=i, version=command.version)
            for i, command in enumerate(validated_commands)
        ]
        self.invalidate_cache(study, invalidate_self_snapshot=True)
        return str(study.id)

    def move_command(
        self,
        study_id: str,
        command_id: str,
        new_index: int,
        params: RequestParameters,
    ) -> None:
        """
        Move command place in the list of command
        Args:
            study_id: study id
            command_id: command_id
            params: request parameters
            new_index: new index of the command
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)

        index = [command.id for command in study.commands].index(command_id)
        if index >= 0 and len(study.commands) > new_index >= 0:
            command = study.commands[index]
            study.commands.pop(index)
            study.commands.insert(new_index, command)
            for idx in range(len(study.commands)):
                study.commands[idx].index = idx
            self.invalidate_cache(study, invalidate_self_snapshot=True)

    def remove_command(self, study_id: str, command_id: str, params: RequestParameters) -> None:
        """
        Remove command
        Args:
            study_id: study id
            command_id: command_id
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)

        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands.pop(index)
            for idx, command in enumerate(study.commands):
                command.index = idx
            self.invalidate_cache(study, invalidate_self_snapshot=True)

    def remove_all_commands(self, study_id: str, params: RequestParameters) -> None:
        """
        Remove all commands
        Args:
            study_id: study id
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)

        study.commands = []
        self.invalidate_cache(study, invalidate_self_snapshot=True)

    def update_command(
        self,
        study_id: str,
        command_id: str,
        command: CommandDTO,
        params: RequestParameters,
    ) -> None:
        """
        Update a command
        Args:
            study_id: study id
            command_id: command id
            command: new command
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)
        command_objs = self._check_commands_validity(study_id, [command])
        validated_commands = transform_command_to_dto(command_objs, [command])
        assert_this(len(validated_commands) == 1)
        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands[index].command = validated_commands[0].action
            study.commands[index].args = json.dumps(validated_commands[0].args)
            self.invalidate_cache(study, invalidate_self_snapshot=True)

    def export_commands_matrices(self, study_id: str, params: RequestParameters) -> FileDownloadTaskDTO:
        study = self._get_variant_study(study_id, params)
        matrices = {
            matrix
            for command in study.commands
            for matrix in suppress_exception(
                lambda: reduce(
                    lambda m, c: m + c.get_inner_matrices(),
                    self.command_factory.to_command(command.to_dto()),
                    t.cast(t.List[str], []),
                ),
                lambda e: logger.warning(f"Failed to parse command {command}", exc_info=e),
            )
            or []
        }
        return t.cast(MatrixService, self.command_factory.command_context.matrix_service).download_matrix_list(
            list(matrices), f"{study.name}_{study.id}_matrices", params
        )

    def _get_variant_study(
        self,
        study_id: str,
        params: RequestParameters,
        raw_study_accepted: bool = False,
    ) -> VariantStudy:
        """
        Get variant study (or RAW study if `raw_study_accepted` is `True`), and check READ permissions.

        Args:
            study_id: The study identifier.
            params: request parameters used for permission check.

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

        assert_permission(params.user, study, StudyPermissionType.READ)
        return study

    def invalidate_cache(
        self,
        variant_study: Study,
        invalidate_self_snapshot: bool = False,
    ) -> None:
        remove_from_cache(self.cache, variant_study.id)
        if isinstance(variant_study, VariantStudy) and variant_study.snapshot and invalidate_self_snapshot:
            variant_study.snapshot.last_executed_command = None
        self.repository.save(
            metadata=variant_study,
            update_modification_date=True,
        )
        for child in self.repository.get_children(parent_id=variant_study.id):
            self.invalidate_cache(child, invalidate_self_snapshot=True)

    def clear_snapshot(self, variant_study: Study) -> None:
        logger.info(f"Clearing snapshot for study {variant_study.id}")
        self.invalidate_cache(variant_study, invalidate_self_snapshot=True)
        shutil.rmtree(self.get_study_path(variant_study), ignore_errors=True)

    def has_children(self, study: VariantStudy) -> bool:
        return self.repository.has_children(study.id)

    def get_all_variants_children(
        self,
        parent_id: str,
        params: RequestParameters,
    ) -> VariantTreeDTO:
        study = self._get_variant_study(parent_id, params, raw_study_accepted=True)

        children_tree = VariantTreeDTO(
            node=self.get_study_information(study),
            children=[],
        )
        children = self.repository.get_children(parent_id=parent_id)
        for child in children:
            try:
                children_tree.children.append(self.get_all_variants_children(child.id, params))
            except UserHasNotPermissionError:
                logger.info(
                    f"Filtering children {child.id} in variant tree since user has not permission on this study"
                )

        return children_tree

    def walk_children(
        self,
        parent_id: str,
        fun: t.Callable[[VariantStudy], None],
        bottom_first: bool,
    ) -> None:
        study = self._get_variant_study(
            parent_id,
            RequestParameters(DEFAULT_ADMIN_USER),
            raw_study_accepted=True,
        )
        children = self.repository.get_children(parent_id=parent_id)
        if not bottom_first:
            fun(study)
        for child in children:
            self.walk_children(child.id, fun, bottom_first)
        if bottom_first:
            fun(study)

    def get_variants_parents(self, id: str, params: RequestParameters) -> t.List[StudyMetadataDTO]:
        output_list: t.List[StudyMetadataDTO] = self._get_variants_parents(id, params)
        if output_list:
            output_list = output_list[1:]
        return output_list

    def get_direct_parent(self, id: str, params: RequestParameters) -> t.Optional[StudyMetadataDTO]:
        study = self._get_variant_study(id, params, raw_study_accepted=True)
        if study.parent_id is not None:
            parent = self._get_variant_study(study.parent_id, params, raw_study_accepted=True)
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

    def _get_variants_parents(self, id: str, params: RequestParameters) -> t.List[StudyMetadataDTO]:
        study = self._get_variant_study(id, params, raw_study_accepted=True)
        metadata = (
            self.get_study_information(
                study,
            )
            if isinstance(study, VariantStudy)
            else self.raw_study_service.get_study_information(
                study,
            )
        )
        output_list: t.List[StudyMetadataDTO] = [metadata]
        if study.parent_id is not None:
            output_list.extend(
                self._get_variants_parents(
                    study.parent_id,
                    params,
                )
            )

        return output_list

    def get(
        self,
        metadata: VariantStudy,
        url: str = "",
        depth: int = 3,
        format: t.Optional[str] = None,
        use_cache: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            format: Indicates the file return format. Can be either Can be 'json', 'arrow' or None. If None, the file will be returned as is.
            use_cache: indicate if cache should be used

        Returns: study data formatted in json
        """
        self._safe_generation(metadata, timeout=60)
        self.repository.refresh(metadata)
        return super().get(metadata=metadata, url=url, depth=depth, format=format, use_cache=use_cache)

    def create_variant_study(self, uuid: str, name: str, params: RequestParameters) -> VariantStudy:
        """
        Create a new variant study.

        Args:
            uuid: The UUID of the parent study.
            name: The name of the new variant study.
            params: The request parameters.

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
                f"The study {study.name} is not managed. Cannot create a variant from it."
                f" It must be imported first."
            )

        assert_permission(params.user, study, StudyPermissionType.READ)
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
            folder=(re.sub(f"/?{study.id}", "", study.folder) if study.folder is not None else None),
            groups=study.groups,  # Create inherit_group boolean
            owner_id=params.user.impersonator if params.user else None,
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
            params.get_user_id(),
        )
        return variant_study

    def generate_task(
        self,
        metadata: VariantStudy,
        denormalize: bool = False,
        from_scratch: bool = False,
    ) -> str:
        study_id = metadata.id
        with FileLock(str(self.config.storage.tmp_dir / f"study-generation-{study_id}.lock")):
            logger.info(f"Starting variant study {study_id} generation")
            self.repository.refresh(metadata)
            if metadata.generation_task:
                try:
                    previous_task = self.task_service.status_task(
                        metadata.generation_task,
                        RequestParameters(DEFAULT_ADMIN_USER),
                    )
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

            def callback(notifier: TaskUpdateNotifier) -> TaskResult:
                generator = SnapshotGenerator(
                    cache=self.cache,
                    raw_study_service=self.raw_study_service,
                    command_factory=self.command_factory,
                    study_factory=self.study_factory,
                    patch_service=self.patch_service,
                    repository=self.repository,
                )
                generate_result = generator.generate_snapshot(
                    study_id,
                    DEFAULT_ADMIN_USER,
                    denormalize=denormalize,
                    from_scratch=from_scratch,
                    notifier=notifier,
                )
                return TaskResult(
                    success=generate_result.success,
                    message=f"{study_id} generated successfully"
                    if generate_result.success
                    else f"{study_id} not generated",
                    return_value=generate_result.json(),
                )

            metadata.generation_task = self.task_service.add_task(
                action=callback,
                name=f"Generation of {metadata.id} study",
                task_type=TaskType.VARIANT_GENERATION,
                ref_id=study_id,
                custom_event_messages=CustomTaskEventMessages(start=metadata.id, running=metadata.id, end=metadata.id),
                request_params=RequestParameters(DEFAULT_ADMIN_USER),
            )
            self.repository.save(metadata)
            return str(metadata.generation_task)

    def generate(
        self,
        variant_study_id: str,
        denormalize: bool,
        from_scratch: bool,
        params: RequestParameters,
    ) -> str:
        # Get variant study
        variant_study = self._get_variant_study(variant_study_id, params)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        return self.generate_task(variant_study, denormalize, from_scratch=from_scratch)

    def generate_study_config(
        self,
        variant_study_id: str,
        params: RequestParameters,
    ) -> t.Tuple[GenerationResultInfoDTO, FileStudyTreeConfig]:
        # Get variant study
        variant_study = self._get_variant_study(variant_study_id, params)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        return self._generate_study_config(variant_study, variant_study, None)

    def _generate_study_config(
        self,
        original_study: VariantStudy,
        metadata: VariantStudy,
        config: t.Optional[FileStudyTreeConfig],
    ) -> t.Tuple[GenerationResultInfoDTO, FileStudyTreeConfig]:
        parent_study = self.repository.get(metadata.parent_id)
        if parent_study is None:
            raise StudyNotFoundError(metadata.parent_id)

        if isinstance(parent_study, RawStudy):
            study = self.study_factory.create_from_fs(
                self.raw_study_service.get_study_path(parent_study),
                parent_study.id,
                output_path=Path(original_study.path) / OUTPUT_RELATIVE_PATH,
                use_cache=False,
            )
            parent_config = study.config
        else:
            res, parent_config = self._generate_study_config(original_study, parent_study, config)
            if res is not None and not res.success:
                return res, parent_config

        # Generate
        res, config = self._generate_config(metadata, parent_config)
        # fix paths
        config.path = Path(metadata.path) / SNAPSHOT_RELATIVE_PATH
        config.study_path = Path(metadata.path)
        return res, config

    def _get_commands_and_notifier(
        self,
        variant_study: VariantStudy,
        notifier: TaskUpdateNotifier,
        from_index: int = 0,
    ) -> t.Tuple[t.List[t.List[ICommand]], t.Callable[[int, bool, str], None]]:
        # Generate
        commands: t.List[t.List[ICommand]] = self._to_commands(variant_study, from_index)

        def notify(command_index: int, command_result: bool, command_message: str) -> None:
            try:
                command_result_obj = CommandResultDTO(
                    study_id=variant_study.id,
                    id=variant_study.commands[from_index + command_index].id,
                    success=command_result,
                    message=command_message,
                )
                notifier(command_result_obj.json())
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_VARIANT_GENERATION_COMMAND_RESULT,
                        payload=command_result_obj,
                        permissions=PermissionInfo.from_study(variant_study),
                        channel=EventChannelDirectory.STUDY_GENERATION + variant_study.id,
                    )
                )
            except Exception as e:
                logger.error(
                    f"Fail to notify command result n°{command_index} for study {variant_study.id}",
                    exc_info=e,
                )

        return commands, notify

    def _to_commands(self, metadata: VariantStudy, from_index: int = 0) -> t.List[t.List[ICommand]]:
        commands: t.List[t.List[ICommand]] = [
            self.command_factory.to_command(command_block.to_dto())
            for index, command_block in enumerate(metadata.commands)
            if from_index <= index
        ]
        return commands

    def _generate_config(
        self,
        variant_study: VariantStudy,
        config: FileStudyTreeConfig,
        notifier: TaskUpdateNotifier = noop_notifier,
    ) -> t.Tuple[GenerationResultInfoDTO, FileStudyTreeConfig]:
        commands, notify = self._get_commands_and_notifier(variant_study=variant_study, notifier=notifier)
        return self.generator.generate_config(commands, config, variant_study, notifier=notify)

    def _generate_snapshot(
        self,
        variant_study: VariantStudy,
        dst_path: Path,
        notifier: TaskUpdateNotifier = noop_notifier,
        from_command_index: int = 0,
    ) -> GenerationResultInfoDTO:
        commands, notify = self._get_commands_and_notifier(
            variant_study=variant_study,
            notifier=notifier,
            from_index=from_command_index,
        )
        return self.generator.generate(commands, dst_path, variant_study, notifier=notify)

    def get_study_task(self, study_id: str, params: RequestParameters) -> TaskDTO:
        """
        Get the generation task ID of a variant study.

        Args:
            study_id: The ID of the variant study.
            params: The request parameters used to check permissions.

        Returns:
            The generation task ID.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
            StudyTypeUnsupported: If the study is not a variant study (HTTP status 422).
            StudyValidationError: If the study has no generation task (HTTP status 422).
        """
        variant_study = self._get_variant_study(study_id, params)
        task_id = variant_study.generation_task
        if task_id:
            return self.task_service.status_task(task_id=task_id, request_params=params, with_logs=True)
        raise StudyValidationError(f"Variant study '{study_id}' has no generation task")

    def create(self, study: VariantStudy) -> VariantStudy:
        """
        Create an empty new study.
        Args:
            study: Study information.
        Returns: New study information.
        """
        raise NotImplementedError()

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

    def copy(
        self,
        src_meta: VariantStudy,
        dest_name: str,
        groups: t.Sequence[str],
        with_outputs: bool = False,
    ) -> VariantStudy:
        """
        Create a new variant study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            with_outputs: Indicates whether to copy the outputs as well.

        Returns:
            The newly created study.
        """
        new_id = str(uuid4())
        study_path = str(self.config.get_workspace_path() / new_id)
        if src_meta.additional_data is None:
            additional_data = StudyAdditionalData()
        else:
            additional_data = StudyAdditionalData(
                horizon=src_meta.additional_data.horizon,
                author=src_meta.additional_data.author,
                patch=src_meta.additional_data.patch,
            )
        dst_meta = VariantStudy(
            id=new_id,
            name=dest_name,
            parent_id=src_meta.parent_id,
            path=study_path,
            public_mode=PublicMode.NONE if groups else PublicMode.READ,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=src_meta.version,
            groups=groups,
            snapshot=None,
            additional_data=additional_data,
        )

        # noinspection PyArgumentList
        dst_meta.commands = [
            CommandBlock(
                study_id=new_id,
                command=command.command,
                args=command.args,
                index=command.index,
                version=command.version,
            )
            for command in src_meta.commands
        ]

        return dst_meta

    def _safe_generation(self, metadata: VariantStudy, timeout: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        try:
            if self.exists(metadata):
                # The study is already present on disk => nothing to do
                return

            logger.info("🔹 Starting variant study generation...")
            # Create and run the generation task in a thread pool.
            task_id = self.generate_task(metadata)
            self.task_service.await_task(task_id, timeout)
            result = self.task_service.status_task(task_id, RequestParameters(DEFAULT_ADMIN_USER))
            if result.result and result.result.success:
                # OK, the study has been generated
                return
            raise ValueError("No task result or result failed")

        except concurrent.futures.TimeoutError as e:
            # Raise a REQUEST_TIMEOUT error (408)
            logger.error(f"⚡ Timeout while generating variant study {metadata.id}", exc_info=e)
            raise VariantGenerationTimeoutError(f"Timeout while generating {metadata.id}") from None

        except Exception as e:
            # raise a EXPECTATION_FAILED error (417)
            logger.error(f"⚡ Fail to generate variant study {metadata.id}", exc_info=e)
            raise VariantGenerationError(f"Error while generating {metadata.id}") from None

    @staticmethod
    def _get_snapshot_last_executed_command_index(
        study: VariantStudy,
    ) -> t.Optional[int]:
        if study.snapshot and study.snapshot.last_executed_command:
            last_executed_command_index = [command.id for command in study.commands].index(
                study.snapshot.last_executed_command
            )
            return last_executed_command_index if last_executed_command_index >= 0 else None
        return None

    def get_raw(
        self,
        metadata: VariantStudy,
        use_cache: bool = True,
        output_dir: t.Optional[Path] = None,
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
            metadata.id,
            output_dir or Path(metadata.path) / "output",
            use_cache=use_cache,
        )

    def get_study_sim_result(self, study: VariantStudy) -> t.List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        self._safe_generation(study, timeout=60)
        return super().get_study_sim_result(study=study)

    def set_reference_output(self, metadata: VariantStudy, output_id: str, status: bool) -> None:
        """
        Set an output to the reference output of a study
        Args:
            metadata: study.
            output_id: the id of output to set the reference status.
            status: true to set it as reference, false to unset it.
        Returns:
        """
        self.patch_service.set_reference_output(metadata, output_id, status)
        remove_from_cache(self.cache, metadata.id)

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

    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        return Path(metadata.path) / SNAPSHOT_RELATIVE_PATH

    def export_study_flat(
        self,
        metadata: VariantStudy,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: t.Optional[t.List[str]] = None,
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
        )

    def get_synthesis(
        self,
        metadata: VariantStudy,
        params: t.Optional[RequestParameters] = None,
    ) -> FileStudyTreeConfigDTO:
        """
        Return study synthesis
        Args:
            metadata: study
            params: RequestParameters
        Returns: FileStudyTreeConfigDTO

        """
        if params is None:
            raise UserHasNotPermissionError()

        results, config = self.generate_study_config(metadata.id, params)
        if results.success:
            return FileStudyTreeConfigDTO.from_build_config(config)

        raise VariantGenerationError(f"Error during light generation of {metadata.id}")

    def initialize_additional_data(self, variant_study: VariantStudy) -> bool:
        try:
            if self.exists(variant_study):
                study = self.study_factory.create_from_fs(
                    self.get_study_path(variant_study),
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
