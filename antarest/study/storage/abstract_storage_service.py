import logging
import shutil
import tempfile
from abc import ABC
from pathlib import Path
from typing import List, Union, Optional, IO
from uuid import uuid4

from antarest.core.config import Config
from antarest.core.exceptions import BadOutputError, StudyOutputNotFoundError
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.model import JSON
from antarest.core.utils.utils import (
    extract_zip,
    StopWatch,
    assert_this,
    zip_dir,
    unzip,
)
from antarest.study.common.studystorage import IStudyStorageService, T
from antarest.study.common.utils import get_study_information
from antarest.study.model import (
    StudyMetadataDTO,
    StudySimResultDTO,
    StudySimSettingsDTO,
    PatchOutputs,
    PatchStudy,
    StudyMetadataPatchDTO,
    StudyAdditionalData,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    get_playlist,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
    FileStudy,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import (
    fix_study_root,
    remove_from_cache,
    extract_output_name,
)

logger = logging.getLogger(__name__)


class AbstractStorageService(IStudyStorageService[T], ABC):
    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        patch_service: PatchService,
        cache: ICache,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.patch_service = patch_service
        self.cache = cache

    def patch_update_study_metadata(
        self,
        study: T,
        metadata: StudyMetadataPatchDTO,
    ) -> StudyMetadataDTO:
        old_patch = self.patch_service.get(study)
        old_patch.study = PatchStudy(
            scenario=metadata.scenario,
            doc=metadata.doc,
            status=metadata.status,
            tags=metadata.tags,
        )
        self.patch_service.save(
            study,
            old_patch,
        )
        remove_from_cache(self.cache, study.id)
        return self.get_study_information(study)

    def get_study_information(
        self,
        study: T,
    ) -> StudyMetadataDTO:
        return get_study_information(study)

    def get(
        self,
        metadata: T,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
        use_cache: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted
            use_cache: indicate if the cache must be used

        Returns: study data formatted in json

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata, use_cache)
        parts = [item for item in url.split("/") if item]

        if url == "" and depth == -1:
            cache_id = f"{CacheConstants.RAW_STUDY}/{metadata.id}"
            from_cache: Optional[JSON] = None
            if use_cache:
                from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Raw Study {metadata.id} read from cache")
                data = from_cache
            else:
                data = study.tree.get(parts, depth=depth, formatted=formatted)
                self.cache.put(cache_id, data)
                logger.info(
                    f"Cache new entry from RawStudyService (studyID: {metadata.id})"
                )
        else:
            data = study.tree.get(parts, depth=depth, formatted=formatted)
        del study
        return data

    def get_study_sim_result(
        self,
        study: T,
    ) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        study_data = self.get_raw(study)
        patch_metadata = self.patch_service.get(study)
        results: List[StudySimResultDTO] = []
        if study_data.config.outputs is not None:
            reference = (patch_metadata.outputs or PatchOutputs()).reference
            for output in study_data.config.outputs:
                output_data: Simulation = study_data.config.outputs[output]
                try:
                    file_metadata = FileStudyHelpers.get_config(
                        study_data, output_data.get_file()
                    )
                    settings = StudySimSettingsDTO(
                        general=file_metadata["general"],
                        input=file_metadata["input"],
                        output=file_metadata["output"],
                        optimization=file_metadata["optimization"],
                        otherPreferences=file_metadata["other preferences"],
                        advancedParameters=file_metadata[
                            "advanced parameters"
                        ],
                        seedsMersenneTwister=file_metadata[
                            "seeds - Mersenne Twister"
                        ],
                        playlist=[
                            year
                            for year in (
                                get_playlist(file_metadata) or {}
                            ).keys()
                        ],
                    )

                    results.append(
                        StudySimResultDTO(
                            name=output_data.get_file(),
                            type=output_data.mode,
                            settings=settings,
                            completionDate="",
                            referenceStatus=(reference == output),
                            synchronized=False,
                            status="",
                            archived=output_data.archived,
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to retrieve info about output {output} in study {study.name} ({study.id}",
                        exc_info=e,
                    )
        return results

    def import_output(
        self,
        metadata: T,
        output: Union[IO[bytes], Path],
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import additional output in an existing study
        Args:
            metadata: study
            output: new output (path or zipped data)
            output_name: optional suffix name to append to output name

        Returns: output id
        """
        path_output = (
            Path(metadata.path) / "output" / f"imported_output_{str(uuid4())}"
        )
        study_id = metadata.id
        path_output.mkdir(parents=True)
        output_full_name: Optional[str] = None
        is_zipped = False
        stopwatch = StopWatch()
        try:
            if isinstance(output, Path):
                if output != path_output and output.suffix != ".zip":
                    shutil.copytree(output, path_output / "imported")
                elif output.suffix == ".zip":
                    is_zipped = True
                    path_output.rmdir()
                    path_output = Path(str(path_output) + ".zip")
                    shutil.copyfile(output, path_output)
            else:
                extract_zip(output, path_output)

            stopwatch.log_elapsed(
                lambda t: logger.info(f"Copied output for {study_id} in {t}s")
            )
            fix_study_root(path_output)
            output_full_name = extract_output_name(path_output, output_name)
            extension = ".zip" if is_zipped else ""
            path_output = path_output.rename(
                Path(path_output.parent, output_full_name + extension)
            )

            data = self.get(
                metadata, f"output/{output_full_name}", 1, use_cache=False
            )

            if data is None:
                self.delete_output(metadata, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output, ignore_errors=True)
            if is_zipped:
                Path(str(path_output) + ".zip").unlink(missing_ok=True)
            output_full_name = None

        return output_full_name

    def export_study(
        self, metadata: T, target: Path, outputs: bool = True
    ) -> Path:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            target: path of the file to export to
            outputs: ask to integrated output folder inside exportation

        Returns: zip file with study files compressed inside

        """
        path_study = Path(metadata.path)
        with tempfile.TemporaryDirectory(
            dir=self.config.storage.tmp_dir
        ) as tmpdir:
            logger.info(f"Exporting study {metadata.id} to tmp path {tmpdir}")
            assert_this(target.name.endswith(".zip"))
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(metadata, tmp_study_path, outputs)
            stopwatch = StopWatch()
            zip_dir(tmp_study_path, target)
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Study {path_study} exported (zipped mode) in {x}s"
                )
            )
        return target

    def export_output(self, metadata: T, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            output_id: output id
            target: path of the file to export to
        """
        logger.info(f"Exporting output {output_id} from study {metadata.id}")

        path_output = Path(metadata.path) / "output" / output_id
        path_output_zip = Path(metadata.path) / "output" / f"{output_id}.zip"

        if path_output_zip.exists():
            shutil.copyfile(path_output_zip, target)
            return None

        if not path_output.exists() and not path_output_zip.exists():
            raise StudyOutputNotFoundError()
        stopwatch = StopWatch()
        if not path_output_zip.exists():
            zip_dir(path_output, target)
        stopwatch.log_elapsed(
            lambda x: logger.info(
                f"Output {output_id} from study {metadata.path} exported in {x}s"
            )
        )

    def _read_additional_data_from_files(
        self, file_study: FileStudy
    ) -> StudyAdditionalData:
        logger.info(
            f"Reading additional data from files for study {file_study.config.study_id}"
        )
        horizon = file_study.tree.get(
            url=["settings", "generaldata", "general", "horizon"]
        )
        author = file_study.tree.get(url=["study", "antares", "author"])
        patch = self.patch_service.get_from_filestudy(file_study)
        study_additional_data = StudyAdditionalData(
            horizon=horizon, author=author, patch=patch.json()
        )
        return study_additional_data

    def archive_study_output(self, study: T, output_id: str) -> bool:
        if not (Path(study.path) / "output" / output_id).exists():
            logger.warning(
                f"Failed to archive study {study.name} output {output_id}. Maybe it's already archived",
            )
            return False
        try:
            zip_dir(
                Path(study.path) / "output" / output_id,
                Path(study.path) / "output" / f"{output_id}.zip",
                remove_source_dir=True,
            )
            remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to archive study {study.name} output {output_id}",
                exc_info=e,
            )
            return False

    def unarchive_study_output(
        self, study: T, output_id: str, keep_src_zip: bool
    ) -> bool:
        if not (Path(study.path) / "output" / f"{output_id}.zip").exists():
            logger.warning(
                f"Failed to archive study {study.name} output {output_id}. Maybe it's already unarchived",
            )
            return False
        try:
            unzip(
                Path(study.path) / "output" / output_id,
                Path(study.path) / "output" / f"{output_id}.zip",
                remove_source_zip=not keep_src_zip,
            )
            remove_from_cache(self.cache, study.id)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to unarchive study {study.name} output {output_id}",
                exc_info=e,
            )
            return False
