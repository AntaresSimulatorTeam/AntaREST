from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List

from antarest.storage.business.rawstudy.model import FileStudy
from antarest.storage.model import Study, StudySimResultDTO, StudyMetadataDTO

T = TypeVar("T", bound=Study)


class IStudyStorageService(ABC, Generic[T]):
    @abstractmethod
    def create(self, metadata: T) -> None:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        raise NotImplementedError()

    @abstractmethod
    def exists(self, metadata: T) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def copy(
        self, src_meta: T, dest_meta: T, with_outputs: bool = False
    ) -> None:
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
        raise NotImplementedError()

    @abstractmethod
    def get_study_sim_result(self, metadata: T) -> List[StudySimResultDTO]:
        raise NotImplementedError()

    @abstractmethod
    def set_reference_output(
        self, metadata: T, output_id: str, status: bool
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, metadata: T) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete_output(self, metadata: T, output_id: str) -> None:
        raise NotImplementedError()
