import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile

from antarest.core.config import Config
from antarest.core.custom_types import JSON, SUB_JSON
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.login.model import GroupDTO
from antarest.study.common.studystorage import (
    IStudyStorageService,
)
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    StudyMetadataPatchDTO,
    StudyMetadataDTO,
    PatchStudy,
    StudySimResultDTO,
    StudySimSettingsDTO,
    PatchOutputs,
    OwnerInfo,
    PublicMode,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
    FileStudy,
)
from antarest.study.storage.rawstudy.patch_service import PatchService
from antarest.study.storage.utils import update_antares_info

logger = logging.getLogger(__name__)


class RawStudyService(IStudyStorageService[RawStudy]):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    new_default_version = 720

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        path_resources: Path,
        patch_service: PatchService,
        cache: ICache,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.path_resources: Path = path_resources
        self.patch_service = patch_service
        self.cache = cache

    def _check_study_exists(self, metadata: RawStudy) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.exists(metadata):
            raise StudyNotFoundError(
                f"Study with the uuid {metadata.id} does not exist."
            )

    def update_from_raw_meta(
        self, metadata: RawStudy, fallback_on_default: Optional[bool] = False
    ) -> None:
        """
        Update metadata from study raw metadata
        Args:
            metadata: study
            fallback_on_default: use default values in case of failure
        """
        path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(path, study_id="")
        try:
            raw_meta = study.get(["study", "antares"])
            metadata.name = raw_meta["caption"]
            metadata.version = raw_meta["version"]
            metadata.created_at = datetime.fromtimestamp(raw_meta["created"])
            metadata.updated_at = datetime.fromtimestamp(raw_meta["lastsave"])
        except Exception as e:
            logger.error(
                "Failed to fetch study %s raw metadata!",
                str(metadata.path),
                exc_info=e,
            )
            if fallback_on_default is not None:
                metadata.name = metadata.name or "unnamed"
                metadata.version = metadata.version or 0
                metadata.created_at = metadata.created_at or datetime.now()
                metadata.updated_at = metadata.updated_at or datetime.now()
            else:
                raise e

    def check_errors(self, metadata: RawStudy) -> List[str]:
        """
        Check study antares data integrity
        Args:
            metadata: study

        Returns: list of non integrity inside study

        """
        path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(path, metadata.id)
        return study.check_errors(study.get())

    def exists(self, metadata: RawStudy) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        return (self.get_study_path(metadata) / "study.antares").is_file()

    def get_raw(self, metadata: RawStudy) -> FileStudy:
        """
        Fetch a study object and its config
        Args:
            metadata: study

        Returns: the config and study tree object

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        study_config, study_tree = self.study_factory.create_from_fs(
            study_path, metadata.id
        )
        return FileStudy(config=study_config, tree=study_tree)

    def get(
        self,
        metadata: RawStudy,
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
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)

        _, study = self.study_factory.create_from_fs(study_path, metadata.id)
        parts = [item for item in url.split("/") if item]

        data: JSON = dict()
        if url == "" and depth == -1:
            cache_id = f"{metadata.id}/{CacheConstants.RAW_STUDY}"
            from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Raw Study {metadata.id} read from cache")
                data = from_cache
            else:
                data = study.get(parts, depth=depth, formatted=formatted)
                self.cache.put(cache_id, data)
                logger.info(
                    f"Cache new entry from RawStudyService (studyID: {metadata.id})"
                )
        else:
            data = study.get(parts, depth=depth, formatted=formatted)
        del study
        return data

    def get_study_information(
        self, study: RawStudy, summary: bool = False
    ) -> StudyMetadataDTO:
        """
        Get information present in study.antares file
        Args:
            study: study
            summary: if true, only retrieve basic info from database

        Returns: study metadata

        """
        file_settings = {}
        file_metadata = {}
        study_path = self.get_study_path(study)
        config = FileStudyTreeConfig(
            study_path=study_path,
            path=study_path,
            study_id="",
            version=-1,
        )
        patch_metadata = self.patch_service.get(study).study or PatchStudy()

        try:
            raw_study = self.study_factory.create_from_config(config)
            file_metadata = raw_study.get(url=["study", "antares"])
            file_settings = raw_study.get(
                url=["settings", "generaldata", "general"]
            )
        except Exception as e:
            logger.error(
                "Failed to retrieve general settings for raw study %s",
                study.id,
                exc_info=e,
            )

        return StudyMetadataDTO(
            id=study.id,
            name=study.name,
            version=study.version,
            created=study.created_at.timestamp(),
            updated=study.updated_at.timestamp(),
            workspace=study.workspace,
            managed=study.workspace == DEFAULT_WORKSPACE_NAME,
            archived=study.archived if study.archived is not None else False,
            owner=OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name=file_metadata.get("author", "Unknown")),
            groups=[
                GroupDTO(id=group.id, name=group.name)
                for group in study.groups
            ],
            public_mode=study.public_mode or PublicMode.NONE,
            horizon=file_settings.get("horizon", None),
            scenario=patch_metadata.scenario,
            status=patch_metadata.status,
            doc=patch_metadata.doc,
        )

    def get_study_path(self, metadata: RawStudy) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        path: Path = Path(metadata.path)
        return path

    def create(self, metadata: RawStudy) -> RawStudy:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        empty_study_zip = self.path_resources / "empty-study.zip"

        path_study = self.get_study_path(metadata)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        _, study = self.study_factory.create_from_fs(path_study, metadata.id)
        update_antares_info(metadata, study)

        metadata.path = str(path_study)
        return metadata

    def copy(
        self,
        src_meta: RawStudy,
        dest_meta: RawStudy,
        with_outputs: bool = False,
    ) -> RawStudy:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study
            with_outputs: indicate weither to copy the output or not

        Returns: destination study

        """
        self._check_study_exists(src_meta)
        src_path = self.get_study_path(src_meta)
        dest_path = self.get_study_path(dest_meta)

        shutil.copytree(src_path, dest_path)

        output = dest_path / "output"
        if not with_outputs and output.exists():
            shutil.rmtree(output)

        _, study = self.study_factory.create_from_fs(
            dest_path, study_id=dest_meta.id
        )
        update_antares_info(dest_meta, study)

        del study
        return dest_meta

    def remove_from_cache(self, root_id: str) -> None:
        self.cache.invalidate_all(
            [
                f"{root_id}/{CacheConstants.RAW_STUDY}",
                f"{root_id}/{CacheConstants.STUDY_FACTORY}",
            ]
        )

    def delete(self, metadata: RawStudy) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        shutil.rmtree(study_path)
        self.remove_from_cache(metadata.id)

    def delete_output(self, metadata: RawStudy, output_name: str) -> None:
        """
        Delete output folder
        Args:
            metadata: study
            output_name: output simulation

        Returns:

        """
        study_path = self.get_study_path(metadata)
        output_path = study_path / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)
        self.remove_from_cache(metadata.id)

    def edit_study(
        self, metadata: RawStudy, url: str, new: SUB_JSON
    ) -> SUB_JSON:
        """
        Replace data on disk with new
        Args:
            metadata: study
            url: data path to reach
            new: new data to replace

        Returns: new data replaced

        """
        # Get data
        self._check_study_exists(metadata)

        study_path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(study_path, metadata.id)
        study.save(new, url.split("/"))  # type: ignore
        del study
        self.remove_from_cache(metadata.id)
        return new

    def patch_update_study_metadata(
        self, study: RawStudy, metadata: StudyMetadataPatchDTO
    ) -> StudyMetadataDTO:
        self.patch_service.patch(
            study,
            {
                "study": {
                    "scenario": metadata.scenario,
                    "doc": metadata.doc,
                    "status": metadata.status,
                }
            },
        )
        self.remove_from_cache(study.id)
        return self.get_study_information(study)

    def set_reference_output(
        self, study: RawStudy, output_id: str, status: bool
    ) -> None:
        self.patch_service.set_reference_output(study, output_id, status)
        self.remove_from_cache(study.id)

    def get_study_sim_result(self, study: RawStudy) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data

        """
        study_path = self.get_study_path(study)
        config, raw_study = self.study_factory.create_from_fs(
            study_path, study.id
        )
        patch_metadata = self.patch_service.get(study)
        results: List[StudySimResultDTO] = []
        if config.outputs is not None:
            reference = (patch_metadata.outputs or PatchOutputs()).reference
            for output in config.outputs:
                file_metadata = raw_study.get(
                    url=["output", output, "about-the-study", "parameters"]
                )
                settings = StudySimSettingsDTO(
                    general=file_metadata["general"],
                    input=file_metadata["input"],
                    output=file_metadata["output"],
                    optimization=file_metadata["optimization"],
                    otherPreferences=file_metadata["other preferences"],
                    advancedParameters=file_metadata["advanced parameters"],
                    seedsMersenneTwister=file_metadata[
                        "seeds - Mersenne Twister"
                    ],
                )
                output_data: Simulation = config.outputs[output]
                results.append(
                    StudySimResultDTO(
                        name=output_data.get_file(),
                        type=output_data.mode,
                        settings=settings,
                        completionDate="",
                        referenceStatus=(reference == output),
                        synchronized=False,
                        status="",
                    )
                )
        return results
