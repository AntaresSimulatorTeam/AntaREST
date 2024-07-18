import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.study.model import Study, StudyMetadataDTO, StudyMetadataPatchDTO, StudySimResultDTO
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

T = t.TypeVar("T", bound=Study)


class IStudyStorageService(ABC, t.Generic[T]):
    @abstractmethod
    def create(self, metadata: T) -> T:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """

    @abstractmethod
    def get(
        self,
        metadata: T,
        url: str = "",
        depth: int = 3,
        format: t.Optional[str] = None,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            format: Indicates the file return format. Can be 'json', 'arrow' or None. If None, the file will be returned as is.

        Returns: study data formatted in json

        """

    @abstractmethod
    def exists(self, metadata: T) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """

    @abstractmethod
    def copy(self, src_meta: T, dest_name: str, groups: t.Sequence[str], with_outputs: bool = False) -> T:
        """
        Create a new study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            with_outputs: Indicates whether to copy the outputs as well.

        Returns:
            The newly created study.
        """

    @abstractmethod
    def patch_update_study_metadata(self, study: T, metadata: StudyMetadataPatchDTO) -> StudyMetadataDTO:
        """
        Update patch study metadata
        Args:
            study: study
            metadata: patch

        Returns: study metadata

        """

    @abstractmethod
    def import_output(
        self,
        study: T,
        output: t.Union[t.BinaryIO, Path],
        output_name: t.Optional[str] = None,
    ) -> t.Optional[str]:
        """
        Import an output
        Args:
            study: the study
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name
        Returns: None
        """

    @abstractmethod
    def get_study_information(self, metadata: T) -> StudyMetadataDTO:
        """Get study information."""

    @abstractmethod
    def get_raw(
        self,
        metadata: T,
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

    @abstractmethod
    def get_study_sim_result(self, metadata: T) -> t.List[StudySimResultDTO]:
        """
        Get global result information

        Args:
            metadata: study

        Returns:
            study output data
        """

    @abstractmethod
    def set_reference_output(self, metadata: T, output_id: str, status: bool) -> None:
        """
        Set an output to the reference output of a study

        Args:
            metadata: study
            output_id: the id of output to set the reference status.
            status: true to set it as reference, false to unset it.
        """

    @abstractmethod
    def delete(self, metadata: T) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """

    @abstractmethod
    def delete_output(self, metadata: T, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation

        Returns:

        """

    @abstractmethod
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """

    def _check_study_exists(self, metadata: Study) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.exists(metadata):
            raise StudyNotFoundError(f"Study with the uuid {metadata.id} does not exist.")

    @abstractmethod
    def export_study(self, metadata: T, target: Path, outputs: bool = True) -> Path:
        """
        Export and compress a study to a ZIP file.

        Args:
            metadata: The study metadata.
            target: The path of the ZIP file to export to.
            outputs: Whether to include the output folder inside the exportation.

        Returns:
            Path: The path to the created ZIP file containing the study files.
        """

    @abstractmethod
    def export_output(self, metadata: T, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside

        """

    @abstractmethod
    def export_study_flat(
        self,
        metadata: T,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: t.Optional[t.List[str]] = None,
        denormalize: bool = True,
    ) -> None:
        """
        Export study to destination

        Args:
            metadata: study.
            dst_path: destination path.
            outputs: list of outputs to keep.
            output_list_filter: list of outputs to keep (None indicate all outputs).
            denormalize: denormalize the study (replace matrix links by real matrices).
        """

    @abstractmethod
    def get_synthesis(self, metadata: T, params: t.Optional[RequestParameters] = None) -> FileStudyTreeConfigDTO:
        """
        Return study synthesis
        Args:
            metadata: study
            params: RequestParameters
        Returns: FileStudyTreeConfigDTO

        """

    @abstractmethod
    def initialize_additional_data(self, study: T) -> bool:
        """Initialize additional data for a study."""

    @abstractmethod
    def archive_study_output(self, study: T, output_id: str) -> bool:
        """Archive a study output."""

    # noinspection SpellCheckingInspection
    @abstractmethod
    def unarchive_study_output(self, study: T, output_id: str, keep_src_zip: bool) -> bool:
        """Un-archive a study output."""
