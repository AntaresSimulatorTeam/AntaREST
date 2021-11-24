import logging
import os
import shutil
import tempfile
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional, IO
from uuid import uuid4

from antarest.core.config import Config
from antarest.core.model import JSON, PublicMode
from antarest.core.exceptions import BadOutputError, StudyOutputNotFoundError
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.utils.utils import extract_zip, StopWatch
from antarest.login.model import GroupDTO
from antarest.study.common.studystorage import IStudyStorageService, T
from antarest.study.model import (
    StudyMetadataDTO,
    StudySimResultDTO,
    StudySimSettingsDTO,
    PatchOutputs,
    OwnerInfo,
    DEFAULT_WORKSPACE_NAME,
    PatchStudy,
    StudyMetadataPatchDTO,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Simulation,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
    FileStudy,
)
from antarest.study.storage.utils import fix_study_root, remove_from_cache

logger = logging.getLogger(__name__)


class AbstractStorageService(IStudyStorageService[T]):
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
        remove_from_cache(self.cache, study.id)
        return self.get_study_information(study)

    def get_study_information(
        self,
        study: T,
        summary: bool = False,
    ) -> StudyMetadataDTO:
        file_settings = {}
        file_metadata = {}

        patch_metadata = PatchStudy()

        if not summary:
            try:
                patch_metadata = (
                    self.patch_service.get(study).study or PatchStudy()
                )
                study_path = self.get_study_path(study)
                if study_path:
                    config = FileStudyTreeConfig(
                        study_path=study_path,
                        path=study_path,
                        study_id="",
                        version=-1,
                    )
                    raw_study = self.study_factory.create_from_config(config)
                    file_metadata = raw_study.get(url=["study", "antares"])
                    file_settings = raw_study.get(
                        url=["settings", "generaldata", "general"]
                    )
            except Exception as e:
                logger.error(
                    "Failed to retrieve general settings for study %s",
                    study.id,
                    exc_info=e,
                )

        study_workspace = DEFAULT_WORKSPACE_NAME
        if hasattr(study, "workspace"):
            study_workspace = study.workspace
        folder: Optional[str] = None
        if hasattr(study, "folder"):
            folder = study.folder

        return StudyMetadataDTO(
            id=study.id,
            name=study.name,
            version=int(study.version),
            created=str(study.created_at),
            updated=str(study.updated_at),
            workspace=study_workspace,
            managed=study_workspace == DEFAULT_WORKSPACE_NAME,
            type=study.type,
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
            folder=folder,
        )

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
                file_metadata = study_data.tree.get(
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
                output_data: Simulation = study_data.config.outputs[output]
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

    def import_output(
        self,
        metadata: T,
        output: Union[IO[bytes], Path],
    ) -> Optional[str]:
        """
        Import additional output on a existing study
        Args:
            metadata: study
            output: new output (path or zipped data)

        Returns: output id
        """
        path_output = (
            Path(metadata.path) / "output" / f"imported_output_{str(uuid4())}"
        )
        os.makedirs(path_output)
        output_name: Optional[str] = None
        try:
            if isinstance(output, Path):
                if output != path_output:
                    shutil.copytree(output, path_output / "imported")
            else:
                extract_zip(output, path_output)

            fix_study_root(path_output)

            ini_reader = IniReader()
            info_antares_output = ini_reader.read(
                path_output / "info.antares-output"
            )["general"]

            date = datetime.fromtimestamp(
                int(info_antares_output["timestamp"])
            ).strftime("%Y%m%d-%H%M")

            mode = "eco" if info_antares_output["mode"] == "Economy" else "adq"
            name = (
                f"-{info_antares_output['name']}"
                if info_antares_output["name"]
                else ""
            )

            output_name = f"{date}{mode}{name}"
            path_output = path_output.rename(
                Path(path_output.parent, output_name)
            )

            data = self.get(
                metadata, f"output/{output_name}", -1, use_cache=False
            )

            if data is None:
                self.delete_output(metadata, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output, ignore_errors=True)
            output_name = None

        return output_name

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
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(metadata, tmp_study_path, outputs)
            stopwatch = StopWatch()
            filename = shutil.make_archive(
                base_name=os.path.splitext(target)[0],
                format="zip",
                root_dir=tmp_study_path,
            )
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Study {path_study} exported (zipped mode) in {x}s"
                )
            )
        return target.parent / filename

    def export_output(self, metadata: T, output_id: str, target: Path) -> Path:
        """
        Export and compresses study inside zip
        Args:
            metadata: study
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside
        """
        logger.info(f"Exporting output {output_id} from study {metadata.id}")

        path_output = Path(metadata.path) / "output" / output_id
        if not path_output.exists():
            raise StudyOutputNotFoundError()
        stopwatch = StopWatch()
        filename = shutil.make_archive(
            base_name=os.path.splitext(target)[0],
            format="zip",
            root_dir=path_output,
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(
                f"Output {output_id} from study {metadata.path} exported in {x}s"
            )
        )
        return target.parent / filename

    @abstractmethod
    def export_study_flat(
        self, metadata: T, dest: Path, outputs: bool = True
    ) -> None:
        raise NotImplementedError()

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
    def copy(
        self, src_meta: T, dest_name: str, with_outputs: bool = False
    ) -> T:
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
    def get_raw(self, metadata: T, use_cache: bool = True) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
            use_cache: indicate if the cache should be used

        Returns: the config and study tree object

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
