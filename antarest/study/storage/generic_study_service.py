import logging
import shutil
from pathlib import Path
from typing import List, Union

from antarest.core.config import Config
from antarest.core.custom_types import JSON
from antarest.core.interfaces.cache import ICache
from antarest.study.common.studystorage import IStudyStorageService, T
from antarest.study.model import (
    Study,
    StudyMetadataDTO,
    StudySimResultDTO,
    RawStudy,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.utils import (
    get_study_information,
    remove_from_cache,
    get_using_cache,
)
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
)
from antarest.study.storage.variantstudy.variant_snapshot_generator import (
    SNAPSHOT_RELATIVE_PATH,
)

logger = logging.getLogger(__name__)


class GenericStudyService(IStudyStorageService[T]):
    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        patch_service: PatchService,
        cache: ICache,
    ):
        self.study_factory = study_factory
        self.patch_service = patch_service
        self.config = config
        self.cache = cache

    def get_study_information(
        self, study: T, summary: bool = False
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
            study.snapshot.path if study.snapshot is not None else None,
            self.patch_service,
            self.study_factory,
            logger,
            summary,
        )

    def get(
        self,
        metadata: T,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted

        Returns: study data formatted in json

        """
        return get_using_cache(
            study_service=self,
            metadata=metadata,
            logger=logger,
            url=url,
            depth=depth,
            formatted=formatted,
        )

    def remove_from_cache(self, root_id: str) -> None:
        remove_from_cache(self.cache, root_id)

    def import_output(self, study: Study, output: Union[bytes, Path]) -> None:
        """
        Import an output
        Args:
            study: the study
            output: Path of the output or raw data
        Returns: None
        """
        raise NotImplementedError()

    def create(self, study: T) -> T:
        """
        Create empty new study
        Args:
            study: study information
        Returns: new study information
        """
        raise NotImplementedError()

    def exists(self, study: T) -> bool:
        """
        Check study exist.
        Args:
            study: study
        Returns: true if study presents in disk, false else.
        """
        raise NotImplementedError()

    def copy(
        self,
        src_meta: T,
        dest_meta: T,
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

    def get_raw(self, metadata: T) -> FileStudy:
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
            metadata: study
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
        study_path = self.get_study_path(metadata)
        if study_path.exists():
            shutil.rmtree(metadata.path)
            self.remove_from_cache(metadata.id)

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
        self.remove_from_cache(metadata.id)
