from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, List

from antarest.study.model import Study, StudySimResultDTO, StudyMetadataDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

T = TypeVar("T", bound=Study)


class IStudyStorageService(ABC, Generic[T]):
    @abstractmethod
    def create(self, metadata: T) -> T:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        raise NotImplementedError()

    @abstractmethod
    def exists(self, metadata: T) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        raise NotImplementedError()

    @abstractmethod
    def copy(self, src_meta: T, dest_meta: T, with_outputs: bool = False) -> T:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study
            with_outputs: indicate either to copy the output or not

        Returns: destination study

        """
        raise NotImplementedError()

    @abstractmethod
    def get_study_information(
        self, metadata: T, summary: bool
    ) -> StudyMetadataDTO:
        raise NotImplementedError()

    @abstractmethod
    def get_raw(self, metadata: T) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study

        Returns: the config and study tree object

        """
        raise NotImplementedError()

    @abstractmethod
    def get_study_sim_result(self, metadata: T) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data

        """
        raise NotImplementedError()

    @abstractmethod
    def set_reference_output(
        self, metadata: T, output_id: str, status: bool
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

    @abstractmethod
    def delete(self, metadata: T) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def delete_output(self, metadata: T, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation

        Returns:

        """
        raise NotImplementedError()

    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        return Path(metadata.path)
