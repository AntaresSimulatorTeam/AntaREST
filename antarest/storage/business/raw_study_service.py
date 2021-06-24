import copy
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from zipfile import ZipFile

from antarest.common.config import Config
from antarest.common.custom_types import JSON, SUB_JSON
from antarest.storage.business.patch_service import PatchService
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.model import (
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    StudyMetadataPatchDTO,
    StudyMetadataDTO,
    Patch,
    PatchStudy,
    StudySimResultDTO,
    StudySimSettingsDTO,
    PatchOutputs,
)
from antarest.storage.repository.filesystem.config.model import (
    StudyConfig,
    Simulation,
)
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.repository.filesystem.root.study import Study
from antarest.storage.web.exceptions import StudyNotFoundError

logger = logging.getLogger(__name__)


class RawStudyService:
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
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.path_resources: Path = path_resources
        self.patch_service = patch_service

    def check_study_exists(self, metadata: RawStudy) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.study_exists(metadata):
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
        _, study = self.study_factory.create_from_fs(path)
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
        _, study = self.study_factory.create_from_fs(path)
        return study.check_errors(study.get())

    def study_exists(self, metadata: RawStudy) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        return (self.get_study_path(metadata) / "study.antares").is_file()

    def get_study(self, metadata: RawStudy) -> Tuple[StudyConfig, Study]:
        """
        Fetch a study object and its config
        Args:
            metadata: study

        Returns: the config and study tree object

        """
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        return self.study_factory.create_from_fs(study_path)

    def get(self, metadata: RawStudy, url: str = "", depth: int = 3) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path

        Returns: study data formatted in json

        """
        _, study = self.get_study(metadata)
        parts = [item for item in url.split("/") if item]

        data = study.get(parts, depth=depth)
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
        config = StudyConfig(study_path=self.get_study_path(study))
        raw_study = self.study_factory.create_from_config(config)
        file_metadata = raw_study.get(url=["study", "antares"])
        patch_metadata = self.patch_service.get(study).study or PatchStudy()

        try:
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
            author=study.owner.name
            if study.owner is not None
            else file_metadata.get("author", "Unknown"),
            horizon=file_settings.get("horizon", None),
            scenario=patch_metadata.scenario,
            status=patch_metadata.status,
            doc=patch_metadata.doc,
        )

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

    def get_study_path(self, metadata: RawStudy) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        path: Path = Path(metadata.path)
        return path

    def create_study(self, metadata: RawStudy) -> RawStudy:
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

        study_data = self.get(metadata, url="", depth=10)
        StorageServiceUtils.update_antares_info(metadata, study_data)

        _, study = self.study_factory.create_from_fs(path_study)
        study.save(study_data["study"], url=["study"])

        metadata.path = str(path_study)
        return metadata

    def copy_study(self, src_meta: RawStudy, dest_meta: RawStudy) -> RawStudy:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study

        Returns: destination study

        """
        self.check_study_exists(src_meta)
        src_path = self.get_study_path(src_meta)

        config, study = self.study_factory.create_from_fs(src_path)
        data_source = study.get()
        del study

        config.path = Path(dest_meta.path)
        data_destination = copy.deepcopy(data_source)

        StorageServiceUtils.update_antares_info(dest_meta, data_destination)
        if "output" in data_destination:
            del data_destination["output"]
        config.outputs = {}

        study = self.study_factory.create_from_config(config)
        study.save(data_destination)
        del study
        return dest_meta

    def delete_study(self, metadata: RawStudy) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        shutil.rmtree(study_path)

    def delete_output(self, metadata: RawStudy, output_name: str) -> None:
        """
        Delete output folder
        Args:
            metadata: study
            output_name: output simulation

        Returns:

        """
        output_path = self.get_study_path(metadata) / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)

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
        self.check_study_exists(metadata)

        study_path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(study_path)
        study.save(new, url.split("/"))  # type: ignore
        del study
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
        return self.get_study_information(study)

    def set_reference_output(self, study: RawStudy, output_id: str) -> None:
        self.patch_service.set_reference_output(study, output_id)

    def get_study_sim_result(self, study: RawStudy) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data

        """
        study_path = self.get_study_path(study)
        config, raw_study = self.study_factory.create_from_fs(study_path)
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
