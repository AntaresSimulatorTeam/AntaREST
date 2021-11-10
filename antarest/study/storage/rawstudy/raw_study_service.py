import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, IO, List
from uuid import uuid4
from zipfile import ZipFile

from antarest.core.config import Config
from antarest.core.custom_types import SUB_JSON
from antarest.core.exceptions import (
    UnsupportedStudyVersion,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.utils import extract_zip
from antarest.study.model import (
    RawStudy,
    DEFAULT_WORKSPACE_NAME,
    Study,
    STUDY_REFERENCE_TEMPLATES,
)
from antarest.study.storage.abstract_storage_service import (
    AbstractStorageService,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
    FileStudy,
)
from antarest.study.storage.utils import (
    update_antares_info,
    get_default_workspace_path,
    fix_study_root,
)

logger = logging.getLogger(__name__)


class RawStudyService(AbstractStorageService[RawStudy]):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        path_resources: Path,
        patch_service: PatchService,
        cache: ICache,
    ):
        super().__init__(
            config=config,
            study_factory=study_factory,
            patch_service=patch_service,
            cache=cache,
        )
        self.path_resources: Path = path_resources

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

    def exists(self, metadata: RawStudy) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        return (self.get_study_path(metadata) / "study.antares").is_file()

    def get_raw(self, metadata: RawStudy, use_cache: bool = True) -> FileStudy:
        """
        Fetch a study object and its config
        Args:
            metadata: study

        Returns: the config and study tree object

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        study_config, study_tree = self.study_factory.create_from_fs(
            study_path, metadata.id, use_cache=use_cache
        )
        return FileStudy(config=study_config, tree=study_tree)

    def create(self, metadata: RawStudy) -> RawStudy:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        version_template: Optional[str] = STUDY_REFERENCE_TEMPLATES.get(
            metadata.version, None
        )
        if version_template is None:
            raise UnsupportedStudyVersion(metadata.version)

        empty_study_zip = self.path_resources / version_template

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
        dest_name: str,
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
        dest_id = str(uuid4())
        dest_study = RawStudy(
            id=dest_id,
            name=dest_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(get_default_workspace_path(self.config) / dest_id),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=src_meta.version,
        )

        src_path = self.get_study_path(src_meta)
        dest_path = self.get_study_path(dest_study)

        shutil.copytree(src_path, dest_path)

        output = dest_path / "output"
        if not with_outputs and output.exists():
            shutil.rmtree(output)

        _, study = self.study_factory.create_from_fs(
            dest_path, study_id=dest_study.id
        )
        update_antares_info(dest_study, study)

        del study
        return dest_study

    def delete(self, metadata: RawStudy) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        shutil.rmtree(study_path, ignore_errors=True)
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

    def import_study(self, metadata: RawStudy, stream: IO[bytes]) -> Study:
        """
        Import study
        Args:
            metadata: study information
            stream: study content compressed in zip file

        Returns: new study information.

        """
        path_study = self.get_study_path(metadata)
        path_study.mkdir()

        try:
            extract_zip(stream, path_study)
            fix_study_root(path_study)
            self.update_from_raw_meta(metadata)

        except Exception as e:
            shutil.rmtree(path_study)
            raise e

        metadata.path = str(path_study)
        return metadata

    def edit_study(
        self,
        metadata: RawStudy,
        url: str,
        new: SUB_JSON,
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

    def export_study_flat(
        self, metadata: RawStudy, dest: Path, outputs: bool = True
    ) -> None:
        path_study = Path(metadata.path)
        start_time = time.time()
        ignore_patterns = (
            (
                lambda directory, contents: ["output"]
                if str(directory) == str(path_study)
                else []
            )
            if not outputs
            else None
        )
        shutil.copytree(src=path_study, dst=dest, ignore=ignore_patterns)
        stop_time = time.time()
        duration = "{:.3f}".format(stop_time - start_time)
        logger.info(f"Study {path_study} exported (flat mode) in {duration}s")
        _, study = self.study_factory.create_from_fs(dest, "", use_cache=False)
        study.denormalize()
        duration = "{:.3f}".format(time.time() - stop_time)
        logger.info(f"Study {path_study} denormalized in {duration}s")

    def check_errors(
        self,
        metadata: RawStudy,
    ) -> List[str]:
        """
        Check study antares data integrity
        Args:
            metadata: study

        Returns: list of non integrity inside study

        """
        path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(path, metadata.id)
        return study.check_errors(study.get())

    def set_reference_output(
        self, study: RawStudy, output_id: str, status: bool
    ) -> None:
        self.patch_service.set_reference_output(study, output_id, status)
        self.remove_from_cache(study.id)

    def archive(self, study: RawStudy) -> None:
        archive_path = self.get_archive_path(study)
        self.export_study(study, archive_path)
        shutil.rmtree(study.path)

    def get_archive_path(self, study: RawStudy) -> Path:
        return Path(self.config.storage.archive_dir / f"{study.id}.zip")

    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        return Path(metadata.path)
