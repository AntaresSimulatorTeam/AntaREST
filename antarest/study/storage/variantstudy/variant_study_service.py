import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast
from uuid import uuid4

from fastapi import HTTPException
from filelock import FileLock  # type: ignore

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
    NoParentStudyError,
    CommandNotFoundError,
    VariantGenerationError,
    VariantStudyParentNotValid,
    CommandNotValid,
    CommandUpdateAuthorizationError,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import (
    IEventBus,
    Event,
    EventType,
    EventChannelDirectory,
)
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import JSON, StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import (
    TaskResult,
    TaskDTO,
    CustomTaskEventMessages,
)
from antarest.core.tasks.service import (
    ITaskService,
    TaskUpdateNotifier,
    noop_notifier,
)
from antarest.study.model import (
    Study,
    StudyMetadataDTO,
    StudySimResultDTO,
)
from antarest.study.storage.abstract_storage_service import (
    AbstractStorageService,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.utils import (
    get_default_workspace_path,
    is_managed,
    remove_from_cache,
    assert_permission,
    create_permission_from_study,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
    CommandBlock,
    VariantStudySnapshot,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
    CommandResultDTO,
    VariantTreeDTO,
)
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)
from antarest.study.storage.variantstudy.variant_command_generator import (
    VariantCommandGenerator,
)

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

    def get_command(
        self, study_id: str, command_id: str, params: RequestParameters
    ) -> CommandDTO:
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
            index = [command.id for command in study.commands].index(
                command_id
            )  # Maybe add Try catch for this
            return cast(CommandDTO, study.commands[index].to_dto())
        except ValueError:
            raise CommandNotFoundError(
                f"Command with id {command_id} not found"
            )

    def get_commands(
        self, study_id: str, params: RequestParameters
    ) -> List[CommandDTO]:
        """
        Get command lists
        Args:
            study_id: study id
            params: request parameters
        Returns: List of commands
        """
        study = self._get_variant_study(study_id, params)
        return [command.to_dto() for command in study.commands]

    def _check_commands_validity(
        self, study_id: str, commands: List[CommandDTO]
    ) -> None:
        for i, command in enumerate(commands):
            try:
                self.command_factory.to_icommand(command)
            except Exception as e:
                logger.error(
                    f"Command at index {i} for study {study_id}", exc_info=e
                )
                raise CommandNotValid(
                    f"Command at index {i} for study {study_id}"
                )

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

    def append_command(
        self, study_id: str, command: CommandDTO, params: RequestParameters
    ) -> str:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            command: new command
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        self._check_update_authorization(study)
        index = len(study.commands)
        new_id = str(uuid4())
        command_block = CommandBlock(
            id=new_id,
            command=command.action,
            study_id=study.id,
            args=json.dumps(command.args),
            index=index,
        )
        study.commands.append(command_block)
        self.repository.save(study, update_modification_date=True)
        return new_id

    def append_commands(
        self,
        study_id: str,
        commands: List[CommandDTO],
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
        self._check_commands_validity(study_id, commands)
        first_index = len(study.commands)
        study.commands.extend(
            [
                CommandBlock(
                    command=command.action,
                    args=json.dumps(command.args),
                    index=(first_index + i),
                )
                for i, command in enumerate(commands)
            ]
        )
        self.repository.save(metadata=study, update_modification_date=True)
        return str(study.id)

    def replace_commands(
        self,
        study_id: str,
        commands: List[CommandDTO],
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
        self._check_commands_validity(study_id, commands)
        study.commands = []
        study.commands.extend(
            [
                CommandBlock(
                    command=command.action,
                    args=json.dumps(command.args),
                    index=i,
                )
                for i, command in enumerate(commands)
            ]
        )
        self.repository.save(metadata=study, update_modification_date=True)
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
            self.repository.save(metadata=study, update_modification_date=True)

    def remove_command(
        self, study_id: str, command_id: str, params: RequestParameters
    ) -> None:
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
            self.repository.save(metadata=study, update_modification_date=True)

    def remove_all_commands(
        self, study_id: str, params: RequestParameters
    ) -> None:
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
        self.repository.save(metadata=study, update_modification_date=True)

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
        self._check_commands_validity(study_id, [command])

        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands[index].command = command.action
            study.commands[index].args = json.dumps(command.args)
            self.repository.save(metadata=study, update_modification_date=True)

    def _get_variant_study(
        self,
        study_id: str,
        params: RequestParameters,
        raw_study_accepted: bool = False,
    ) -> VariantStudy:
        """
        Get variant study and check permissions
        Args:
            study_id: study id
            params: request parameters
        Returns: None
        """
        study = self.repository.get(study_id)

        if study is None:
            raise StudyNotFoundError(study_id)

        if not isinstance(study, VariantStudy) and not raw_study_accepted:
            raise StudyTypeUnsupported(study_id, study.type)

        assert_permission(params.user, study, StudyPermissionType.READ)
        return study

    def get_all_variants_children(
        self, parent_id: str, params: RequestParameters
    ) -> VariantTreeDTO:
        study = self._get_variant_study(
            parent_id, params, raw_study_accepted=True
        )
        children_tree = VariantTreeDTO(
            node=self.get_study_information(study, summary=True), children=[]
        )
        children = self._get_variants_children(parent_id, params)
        for child in children:
            children_tree.children.append(
                self.get_all_variants_children(child.id, params)
            )

        return children_tree

    def _get_variants_children(
        self, parent_id: str, params: RequestParameters
    ) -> List[StudyMetadataDTO]:
        self._get_variant_study(
            parent_id, params, raw_study_accepted=True
        )  # check permissions
        children = self.repository.get_children(parent_id=parent_id)
        output_list: List[StudyMetadataDTO] = []
        for child in children:
            output_list.append(
                self.get_study_information(
                    child,
                    summary=True,
                )
            )

        return output_list

    def get_variants_parents(
        self, id: str, params: RequestParameters
    ) -> List[StudyMetadataDTO]:
        output_list: List[StudyMetadataDTO] = self._get_variants_parents(
            id, params
        )
        if len(output_list) > 0:
            output_list = output_list[1:]
        return output_list

    def _get_variants_parents(
        self, id: str, params: RequestParameters
    ) -> List[StudyMetadataDTO]:
        study = self._get_variant_study(id, params, raw_study_accepted=True)
        metadata = (
            self.get_study_information(
                study,
                summary=True,
            )
            if isinstance(study, VariantStudy)
            else self.raw_study_service.get_study_information(
                study,
                summary=True,
            )
        )
        output_list: List[StudyMetadataDTO] = [metadata]
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
        self._safe_generation(metadata, timeout=30)
        self.repository.refresh(metadata)
        return super().get(
            metadata=metadata,
            url=url,
            depth=depth,
            formatted=formatted,
            use_cache=use_cache,
        )

    def create_variant_study(
        self, uuid: str, name: str, params: RequestParameters
    ) -> Optional[str]:
        """
        Create empty study
        Args:
            uuid: study name to set
            name: name of study
            params: request parameters

        Returns: new study uuid

        """
        study = self.repository.get(uuid)

        if study is None:
            raise StudyNotFoundError(uuid)

        if not is_managed(study):
            raise VariantStudyParentNotValid(
                f"The study {study.name} is not managed. Cannot create a variant from it. It must be imported first."
            )

        assert_permission(params.user, study, StudyPermissionType.READ)
        new_id = str(uuid4())
        study_path = str(get_default_workspace_path(self.config) / new_id)
        variant_study = VariantStudy(
            id=new_id,
            name=name,
            parent_id=uuid,
            path=study_path,
            public_mode=study.public_mode,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=study.version,
            groups=study.groups,  # Create inherit_group boolean
            owner_id=params.user.impersonator if params.user else None,
            snapshot=None,
        )
        self.repository.save(variant_study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=variant_study.to_json_summary(),
                permissions=create_permission_from_study(variant_study),
            )
        )
        logger.info(
            "variant study %s created by user %s",
            variant_study.id,
            params.get_user_id(),
        )
        return str(variant_study.id)

    def generate_task(
        self, metadata: VariantStudy, denormalize: bool = False
    ) -> str:
        with FileLock(
            str(
                self.config.storage.tmp_dir
                / f"study-generation-{metadata.id}.lock"
            )
        ):
            logger.info(f"Starting variant study {metadata.id} generation")
            self.repository.refresh(metadata)
            if metadata.generation_task:
                try:
                    previous_task = self.task_service.status_task(
                        metadata.generation_task,
                        RequestParameters(DEFAULT_ADMIN_USER),
                    )
                    if not previous_task.status.is_final():
                        logger.info(
                            f"Returning already existing variant study {metadata.id} generation"
                        )
                        return str(metadata.generation_task)
                except HTTPException as e:
                    logger.warning(
                        f"Failed to retrieve generation task for study {metadata.id}",
                        exc_info=e,
                    )

            # this is important because the callback will be called outside of the current db context so we need to fetch the id attribute before
            study_id = metadata.id

            def callback(notifier: TaskUpdateNotifier) -> TaskResult:
                generate_result = self._generate(
                    study_id,
                    denormalize,
                    RequestParameters(DEFAULT_ADMIN_USER),
                    notifier,
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
                custom_event_messages=CustomTaskEventMessages(
                    start=metadata.id, running=metadata.id, end=metadata.id
                ),
                request_params=RequestParameters(DEFAULT_ADMIN_USER),
            )
            self.repository.save(metadata)
            return str(metadata.generation_task)

    def generate(
        self,
        variant_study_id: str,
        denormalize: bool,
        params: RequestParameters,
    ) -> str:
        # Get variant study
        variant_study = self._get_variant_study(variant_study_id, params)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        return self.generate_task(variant_study, denormalize)

    def _generate(
        self,
        variant_study_id: str,
        denormalize: bool,
        params: RequestParameters,
        notifier: TaskUpdateNotifier = noop_notifier,
    ) -> GenerationResultInfoDTO:
        logger.info(f"Generating variant study {variant_study_id}")

        # Get variant study
        variant_study = self._get_variant_study(variant_study_id, params)

        # Get parent study
        if variant_study.parent_id is None:
            raise NoParentStudyError(variant_study_id)

        parent_study = self.repository.get(variant_study.parent_id)
        if parent_study is None:
            raise StudyNotFoundError(variant_study.parent_id)

        # Check parent study permission
        assert_permission(params.user, parent_study, StudyPermissionType.READ)

        # Remove from cache
        remove_from_cache(self.cache, variant_study.id)

        # Remove snapshot directory if it exist
        dest_path = self.get_study_path(variant_study)

        variant_study.snapshot = None
        self.repository.save(variant_study, update_modification_date=False)

        if dest_path.is_dir():
            shutil.rmtree(dest_path)

        if isinstance(parent_study, VariantStudy):
            self._safe_generation(parent_study)
            self.export_study_flat(
                metadata=parent_study, dest=dest_path, outputs=False
            )
        else:
            self.raw_study_service.export_study_flat(
                metadata=parent_study, dest=dest_path, outputs=False
            )

        results = self._generate_snapshot(variant_study, notifier)

        if results.success:
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study.id,
                created_at=datetime.utcnow(),
            )
            self.repository.save(variant_study)
            logger.info(f"Saving new snapshot for study {variant_study.id}")
            if denormalize:
                config, study_tree = self.study_factory.create_from_fs(
                    self.get_study_path(variant_study),
                    study_id=variant_study.id,
                )
                logger.info(f"Denormalizing variant study {variant_study.id}")
                study_tree.denormalize()
        return results

    def _generate_snapshot(
        self,
        variant_study: VariantStudy,
        notifier: TaskUpdateNotifier = noop_notifier,
    ) -> GenerationResultInfoDTO:

        # Copy parent study to dest
        dest_path = Path(variant_study.path) / SNAPSHOT_RELATIVE_PATH

        # Generate
        commands: List[List[ICommand]] = []
        for command_block in variant_study.commands:
            commands.append(
                self.command_factory.to_icommand(command_block.to_dto())
            )

        def notify(
            command_index: int, command_result: bool, command_message: str
        ) -> None:
            try:
                command_result_obj = CommandResultDTO(
                    study_id=variant_study.id,
                    id=variant_study.commands[command_index].id,
                    success=command_result,
                    message=command_message,
                )
                notifier(command_result_obj.json())
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_VARIANT_GENERATION_COMMAND_RESULT,
                        payload=command_result_obj,
                        channel=EventChannelDirectory.STUDY_GENERATION
                        + variant_study.id,
                    )
                )
            except Exception as e:
                logger.error(
                    f"Fail to notify command result n°{command_index} for study {variant_study.id}",
                    exc_info=e,
                )

        return self.generator.generate(
            commands, dest_path, variant_study, notifier=notify
        )

    def get_study_task(
        self, study_id: str, params: RequestParameters
    ) -> TaskDTO:
        variant_study = self._get_variant_study(study_id, params)
        task_id = variant_study.generation_task
        return self.task_service.status_task(
            task_id=task_id, request_params=params, with_logs=True
        )

    def create(self, study: VariantStudy) -> VariantStudy:
        """
        Create empty new study
        Args:
            study: study information
        Returns: new study information
        """
        raise NotImplementedError()

    def exists(self, metadata: VariantStudy) -> bool:
        """
        Check study exist.
        Args:
            metadata: study
        Returns: true if study presents in disk, false else.
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
        with_outputs: bool = False,
    ) -> VariantStudy:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study
            with_outputs: indicate either to copy the output or not
        Returns: destination study
        """
        new_id = str(uuid4())
        study_path = str(get_default_workspace_path(self.config) / new_id)
        dest_meta = VariantStudy(
            id=new_id,
            name=dest_name,
            parent_id=src_meta.parent_id,
            path=study_path,
            public_mode=src_meta.public_mode,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=src_meta.version,
            groups=src_meta.groups,  # Create inherit_group boolean
            snapshot=None,
        )

        dest_meta.commands = [
            CommandBlock(
                study_id=new_id,
                command=command.command,
                args=command.args,
                index=command.index,
                version=command.version,
            )
            for command in src_meta.commands
        ]

        return dest_meta

    def _wait_for_generation(
        self, metadata: VariantStudy, timeout: Optional[int] = None
    ) -> bool:
        task_id = self.generate_task(metadata)
        self.task_service.await_task(task_id, timeout)
        result = self.task_service.status_task(
            task_id, RequestParameters(DEFAULT_ADMIN_USER)
        )
        return (result.result is not None) and result.result.success

    def _safe_generation(
        self, metadata: VariantStudy, timeout: Optional[int] = None
    ) -> None:
        try:
            if not self.exists(metadata):
                if not self._wait_for_generation(metadata, timeout):
                    raise ValueError()
        except Exception as e:
            logger.error(
                f"Fail to generate variant study {metadata.id}", exc_info=e
            )
            raise VariantGenerationError(
                f"Error while generating {metadata.id}"
            )

    def get_raw(
        self, metadata: VariantStudy, use_cache: bool = True
    ) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
        Returns: the config and study tree object
        """
        self._safe_generation(metadata)

        study_path = self.get_study_path(metadata)
        study_config, study_tree = self.study_factory.create_from_fs(
            study_path,
            metadata.id,
            Path(metadata.path) / "output",
            use_cache=use_cache,
        )
        return FileStudy(config=study_config, tree=study_tree)

    def get_study_sim_result(
        self, study: VariantStudy
    ) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        self._safe_generation(study, timeout=30)
        return super().get_study_sim_result(study=study)

    def set_reference_output(
        self, metadata: VariantStudy, output_id: str, status: bool
    ) -> None:
        """
        Set an output to the reference output of a study
        Args:
            metadata: study
            output_id: the id of output to set the reference status
            status: true to set it as reference, false to unset it
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
        self, metadata: VariantStudy, dest: Path, outputs: bool = True
    ) -> None:

        self._safe_generation(metadata)
        path_study = Path(metadata.path)
        start_time = time.time()

        snapshot_path = path_study / SNAPSHOT_RELATIVE_PATH
        output_src_path = path_study / "output"
        output_dest_path = dest / "output"
        shutil.copytree(src=snapshot_path, dst=dest)

        if outputs and output_src_path.is_dir():
            if output_dest_path.is_dir():
                shutil.rmtree(output_dest_path)
            shutil.copytree(src=output_src_path, dst=output_dest_path)

        stop_time = time.time()
        duration = "{:.3f}".format(stop_time - start_time)
        logger.info(f"Study {path_study} exported (flat mode) in {duration}s")
        _, study = self.study_factory.create_from_fs(dest, "", use_cache=False)
        study.denormalize()
        duration = "{:.3f}".format(time.time() - stop_time)
        logger.info(f"Study {path_study} denormalized in {duration}s")
