from pathlib import Path
from typing import List, Union

from antarest.core.interfaces.cache import ICache
from antarest.study.common.studystorage import IStudyStorageService
from antarest.study.model import (
    Study,
    StudyMetadataDTO,
    StudySimResultDTO,
    RawStudy,
)

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.db.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model import CommandDTO
from antarest.study.storage.variantstudy.repository import (
    VariantStudyCommandRepository,
)


class VariantStudyService(IStudyStorageService[VariantStudy]):
    def __init__(self, repository: VariantStudyCommandRepository):
        self.raw_study_manager = "RawStudyManager"  # Temporary
        self.generator = "VariantSnapshotGenerator"
        self.repository = repository

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
