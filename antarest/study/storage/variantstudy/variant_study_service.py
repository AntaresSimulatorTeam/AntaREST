import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional, cast
from uuid import uuid4

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
    NoParentStudyError,
    CommandNotFoundError,
)
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.requests import RequestParameters
from antarest.study.common.studystorage import IStudyStorageService
from antarest.study.model import (
    Study,
    StudyMetadataDTO,
    StudySimResultDTO,
    RawStudy,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.permissions import (
    assert_permission,
    StudyPermissionType,
)
from antarest.study.storage.rawstudy.exporter_service import ExporterService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.utils import (
    get_default_workspace_path,
    get_study_information,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
    CommandBlock,
    VariantStudySnapshot,
)
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)
from antarest.study.storage.variantstudy.variant_snapshot_generator import (
    VariantSnapshotGenerator,
    SNAPSHOT_RELATIVE_PATH,
)

logger = logging.getLogger(__name__)


class VariantStudyService(IStudyStorageService[VariantStudy]):
    def __init__(
        self,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        patch_service: PatchService,
        exporter_service: ExporterService,
        repository: VariantStudyRepository,
        event_bus: IEventBus,
        config: Config,
    ):
        self.generator = VariantSnapshotGenerator(
            command_factory, study_factory, exporter_service
        )
        self.study_factory = study_factory
        self.patch_service = patch_service
        self.repository = repository
        self.event_bus = event_bus
        self.config = config

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

    def append_command(
        self, study_id: str, command: CommandDTO, params: RequestParameters
    ) -> None:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            command: new command
            params: request parameters
        Returns: None
        """
        study = self._get_variant_study(study_id, params)
        index = len(study.commands)
        study.commands.append(
            CommandBlock(
                command=command.action,
                args=json.dumps(command.args),
                index=index,
            )
        )
        self.repository.save(study)

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
        self.repository.save(study)
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
        index = [command.id for command in study.commands].index(command_id)
        if index >= 0 and len(study.commands) > new_index >= 0:
            command = study.commands[index]
            study.commands.pop(index)
            study.commands.insert(new_index, command)
            for idx in range(len(study.commands)):
                study.commands[idx].index = idx
            self.repository.save(study)

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
        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands.pop(index)
            self.repository.save(study)

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
        index = [command.id for command in study.commands].index(command_id)
        if index >= 0:
            study.commands[index].command = command.action
            study.commands[index].args = json.dumps(command.args)
            self.repository.save(study)

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

    def get_variants_children(
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

    def get_study_information(
        self, study: VariantStudy, summary: bool = False
    ) -> StudyMetadataDTO:
        """
        Get information present in study.antares file
        Args:
            study: study
            summary: if true, only retrieve basic info from database

        Returns: study metadata

        """
        return get_study_information(
            study,
            self.patch_service,
            self.study_factory,
            logger,
            summary,
        )

    def get_study(self, study_id: str) -> FileStudy:
        """
        Get study
        Args:
            study_id: study id
        Returns: Study
        """
        raise NotImplementedError()

    def import_output(self, study: Study, output: Union[bytes, Path]) -> None:
        """
        Import an output
        Args:
            study: the study
            output: Path of the output or raw data
        Returns: None
        """
        raise NotImplementedError()

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

        assert_permission(params.user, study, StudyPermissionType.READ)
        new_id = str(uuid4())
        study_path = str(get_default_workspace_path(self.config) / new_id)
        variant_study = VariantStudy(
            id=new_id,
            name=name,
            parent_id=uuid,
            path=study_path,
            public_mode=study.public_mode,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=study.version,
            groups=study.groups,  # Create inherit_group boolean
            owner_id=params.user.id if params.user else None,
            snapshot=None,
        )
        self.repository.save(variant_study)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, variant_study.to_json_summary())
        )
        logger.info(
            "variant study %s created by user %s",
            variant_study.id,
            params.get_user_id(),
        )
        return str(variant_study.id)

    def generate(
        self, variant_study_id: str, params: RequestParameters
    ) -> GenerationResultInfoDTO:

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
        if not isinstance(parent_study, RawStudy):
            raise StudyTypeUnsupported(parent_study.id, parent_study.type)

        results = self.generator.generate_snapshot(variant_study, parent_study)
        if results.success:
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study.id,
                path=variant_study.path,
                created_at=datetime.now(),
            )
            self.repository.save(variant_study)
        return results

    def create(self, study: VariantStudy) -> VariantStudy:
        """
        Create empty new study
        Args:
            study: study information
        Returns: new study information
        """
        raise NotImplementedError()

    def exists(self, study: VariantStudy) -> bool:
        """
        Check study exist.
        Args:
            study: study
        Returns: true if study presents in disk, false else.
        """
        raise NotImplementedError()

    def copy(
        self,
        src_meta: VariantStudy,
        dest_meta: VariantStudy,
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
        raise NotImplementedError()

    def get_raw(self, metadata: VariantStudy) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
        Returns: the config and study tree object
        """
        raise NotImplementedError()

    def get_study_sim_result(
        self, metadata: VariantStudy
    ) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def delete(self, metadata: VariantStudy) -> None:
        """
        Delete study
        Args:
            metadata: study
        Returns:
        """
        raise NotImplementedError()

    def delete_output(self, metadata: VariantStudy, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation
        Returns:
        """
        raise NotImplementedError()

    def get_study_path(self, metadata: Study) -> Path:
        return Path(metadata.path) / SNAPSHOT_RELATIVE_PATH
