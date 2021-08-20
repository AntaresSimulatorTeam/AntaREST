from datetime import datetime
import logging
from pathlib import Path
from typing import List, Union, Optional
from uuid import uuid4

from antarest.core.config import Config
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.requests import RequestParameters
from antarest.study.common.studystorage import IStudyStorageService
from antarest.study.model import (
    Study,
    StudyMetadataDTO,
    StudySimResultDTO,
    DEFAULT_WORKSPACE_NAME,
)
from antarest.study.storage.permissions import (
    assert_permission,
    StudyPermissionType,
)

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model import CommandDTO
from antarest.study.storage.variantstudy.model.db.dbmodel import VariantStudy  # type: ignore
from antarest.study.storage.variantstudy.repository import (
    VariantStudyCommandRepository,
)

logger = logging.getLogger(__name__)


class VariantStudyService(IStudyStorageService[VariantStudy]):
    def __init__(
        self,
        repository: VariantStudyCommandRepository,
        event_bus: IEventBus,
        config: Config,
    ):
        self.raw_study_manager = "RawStudyManager"  # Temporary
        self.generator = "VariantSnapshotGenerator"
        self.repository = repository
        self.event_bus = event_bus
        self.config = config

    def get_commands(self, study_id: str) -> List[CommandDTO]:  # List[Command]
        """
        Get command lists
        Args:
            study_id: study id
        Returns: List of commands
        """
        raise NotImplementedError()

    def append_command(self, study_id: str, command: CommandDTO) -> None:
        """
        Add command to list of commands (at the end)
        Args:
            study_id: study id
            command: new command
        Returns: None
        """
        raise NotImplementedError()

    def move_command(
        self, study_id: str, command_id: str, new_parent_id: str
    ) -> None:
        """
        Move command place in the list of command
        Args:
            study_id: study id
            command_id: command_id
            new_parent_id: new parent id of the command
        Returns: None
        """
        raise NotImplementedError()

    def remove_command(self, study_id: str, command_id: str) -> None:
        """
        Remove command
        Args:
            study_id: study id
            command_id: command_id
        Returns: None
        """
        raise NotImplementedError()

    def update_command(
        self, study_id: str, command_id: str, command: CommandDTO
    ) -> None:
        """
        Update a command
        Args:
            study_id: study id
            command_id: command id
            command: new command
        Returns: None
        """
        raise NotImplementedError()

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
        study_path = str(self.get_default_workspace_path() / new_id)
        variant_study = VariantStudy(
            id=new_id,
            name=name,
            parent_id=uuid,
            workspace=study_path,
            path=study_path,
            public_mode=study.public_mode,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=study.version,
            groups=study.groups,  # Create inherit_group boolean
            owner=params.user,
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

    def get_workspace_path(self, workspace: str) -> Path:
        """
        Retrieve workspace path from config

        Args:
            workspace: workspace name

        Returns: path

        """
        return self.config.storage.workspaces[workspace].path

    def get_default_workspace_path(self) -> Path:
        """
        Get path of default workspace
        Returns: path

        """
        return self.get_workspace_path(DEFAULT_WORKSPACE_NAME)

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

    def get_study_information(
        self, metadata: VariantStudy, summary: bool
    ) -> StudyMetadataDTO:
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
