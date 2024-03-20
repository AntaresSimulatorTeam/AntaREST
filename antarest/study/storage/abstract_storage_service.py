import json
import logging
import shutil
import tempfile
import typing as t
from abc import ABC
from enum import Enum
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from antarest.core.config import Config
from antarest.core.exceptions import BadOutputError, StudyOutputNotFoundError
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.model import JSON, PublicMode
from antarest.core.utils.utils import StopWatch, extract_zip, unzip, zip_dir
from antarest.login.model import GroupDTO
from antarest.study.common.default_values import QueryFile
from antarest.study.common.studystorage import IStudyStorageService, T
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Patch,
    PatchOutputs,
    PatchStudy,
    StudyAdditionalData,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
    StudySimResultDTO,
    StudySimSettingsDTO,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.folder_node import ChildNotFoundError
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import extract_output_name, fix_study_root, remove_from_cache

logger = logging.getLogger(__name__)

TEMPLATE_PARTS = "output/{sim_id}/economy/mc-ind"
# noinspection SpellCheckingInspection
MCYEAR_COL = "mcYear"
MC_YEAR_INDEX = 0
FILE_TYPE_1_INDEX = 1
"""
Index in path parts starting from the Monte Carlo year to determine the if we fetch links, areas or binding constraints.
"""
FILE_TYPE_2_INDEX = -2
"""Index in path parts starting from the Monte Carlo year to determine the if we fetch values, details etc ."""
AREA_NAME_INDEX = 2
"""Index in path parts starting from the Monte Carlo year to determine the area name."""
FREQUENCY_INDEX = -2
"""Index in path parts starting from the Monte Carlo year to determine matrix frequency."""


class FileType1(str, Enum):
    """
    Enum to determine the type of file we want to fetch in the study
    """

    LINKS = "links"
    AREAS = "areas"
    BINDING_CONSTRAINTS = "binding_constraints"


class FileType2(str, Enum):
    """
    Enum to determine the type of file we want to fetch in the study
    """

    VALUES = "values"
    DETAILS = "details"
    # noinspection SpellCheckingInspection
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    BINDING_CONSTRAINTS = "binding-constraints"


def stringify(col: t.Union[str, t.Tuple[str, ...]]) -> str:
    """
    Convert a column name from Generic Hashable to a string without comers
    Args:
        col: column name to convert

    Returns:  column name as string

    """
    return "|".join(col) if isinstance(col, tuple) else col


def flatten_tree(path_tree: t.Dict[str, t.Any]) -> t.List[t.Tuple[str, ...]]:
    """
    Flatten paths tree
    Args:
        path_tree: tree to flatten

    Returns: list of tuple with all tree paths parts

    """
    result = []
    for key, value in path_tree.items():
        if isinstance(value, dict):
            result.extend([(key,) + sub for sub in flatten_tree(value)])
        else:
            result.append((key, value))
    return result


def parts_query_file_filtering(
    parts: t.List[t.Tuple[str, ...]], query_file: QueryFile
) -> t.Tuple[FileType1, FileType2, t.List[t.Tuple[str, ...]]]:
    """
    Filter parts list
    Args:
        parts: list of tuple with all tree paths parts
        query_file: query file to filter

    Returns: filtered list of tuple with all tree paths parts

    """
    if query_file == QueryFile.LINKS_VALUES:
        return (
            FileType1.LINKS,
            FileType2.VALUES,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.LINKS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.VALUES)
            ],
        )
    if query_file == QueryFile.LINKS_DETAILS:
        return (
            FileType1.LINKS,
            FileType2.DETAILS,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.LINKS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS)
            ],
        )
    if query_file == QueryFile.AREAS_VALUES:
        return (
            FileType1.AREAS,
            FileType2.VALUES,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.AREAS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.VALUES)
            ],
        )
    if query_file == QueryFile.AREAS_DETAILS:
        return (
            FileType1.AREAS,
            FileType2.DETAILS,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.AREAS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS)
                and not path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS_ST_STORAGE)
                and not path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS_RES)
            ],
        )
    if query_file == QueryFile.AREAS_DETAILS_ST_STORAGE:
        return (
            FileType1.AREAS,
            FileType2.DETAILS_ST_STORAGE,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.AREAS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS_ST_STORAGE)
            ],
        )
    if query_file == QueryFile.AREAS_DETAILS_RES:
        return (
            FileType1.AREAS,
            FileType2.DETAILS_RES,
            [
                path_parts
                for path_parts in parts
                if path_parts[FILE_TYPE_1_INDEX] == FileType1.AREAS
                and path_parts[FILE_TYPE_2_INDEX].startswith(FileType2.DETAILS_RES)
            ],
        )
    if query_file == QueryFile.BINDING_CONSTRAINTS:
        return (
            FileType1.BINDING_CONSTRAINTS,
            FileType2.BINDING_CONSTRAINTS,
            [path_parts for path_parts in parts if path_parts[FILE_TYPE_1_INDEX] == FileType1.BINDING_CONSTRAINTS],
        )

    raise ValueError(f"Unknown query file {query_file}")


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
        additional_data = study.additional_data or StudyAdditionalData()

        try:
            patch_obj = json.loads(additional_data.patch or "{}")
            patch = Patch.parse_obj(patch_obj)
        except ValueError as e:
            # The conversion to JSON and the parsing can fail if the patch is not valid
            logger.warning(f"Failed to parse patch for study {study.id}", exc_info=e)
            patch = Patch()

        patch_metadata = patch.study or PatchStudy()

        study_workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
        folder: t.Optional[str] = None
        if hasattr(study, "folder"):
            folder = study.folder

        owner_info = (
            OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name=additional_data.author or "Unknown")
        )

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
            owner=owner_info,
            groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
            public_mode=study.public_mode or PublicMode.NONE,
            horizon=additional_data.horizon,
            scenario=patch_metadata.scenario,
            status=patch_metadata.status,
            doc=patch_metadata.doc,
            folder=folder,
            tags=[tag.label for tag in study.tags],
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
            from_cache: t.Optional[JSON] = None
            if use_cache:
                from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Raw Study {metadata.id} read from cache")
                data = from_cache
            else:
                data = study.tree.get(parts, depth=depth, formatted=formatted)
                self.cache.put(cache_id, data)
                logger.info(f"Cache new entry from RawStudyService (studyID: {metadata.id})")
        else:
            data = study.tree.get(parts, depth=depth, formatted=formatted)
        del study
        return data

    def aggregate_data(
        self,
        metadata: T,
        output_name: str,
        query_file: QueryFile,
        frequency: MatrixFrequency,
        mc_years: t.Sequence[str],
        areas_names: t.Sequence[str],
        columns_names: t.Sequence[str],
    ) -> t.Dict[str, t.Any]:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            output_name:
            query_file:
            frequency:
            mc_years:
            areas_names:
            columns_names:

        Returns: study data formatted in json

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata)
        parts = TEMPLATE_PARTS.format(sim_id=output_name).split("/")
        file_type_1, _, all_paths = parts_query_file_filtering(flatten_tree(study.tree.get(parts)), query_file)
        if mc_years:
            all_paths = [path_parts for path_parts in all_paths if path_parts[MC_YEAR_INDEX] in mc_years]
        if areas_names and file_type_1 != FileType1.AREAS:
            raise ValueError(f"You specified areas names for a query file that does not support it: {query_file}")
        elif areas_names:
            all_paths = [path_parts for path_parts in all_paths if path_parts[AREA_NAME_INDEX] in areas_names]
        all_paths = [path_parts for path_parts in all_paths if frequency.value in path_parts[FREQUENCY_INDEX]]

        final_df = None
        for path_parts in all_paths:
            try:
                node_data = study.tree.get(parts + list(path_parts[:-1]))
            except ChildNotFoundError:
                continue

            columns, matrix = node_data["columns"], np.array(node_data["data"]).T.tolist()
            columns = [stringify(col) for col in columns]
            kept_columns = [col for col in columns if col in columns_names] if columns_names else columns
            node_data = (
                {file_type_1.value: [path_parts[FILE_TYPE_1_INDEX + 1]] * len(matrix[0])}
                if file_type_1 != FileType1.BINDING_CONSTRAINTS
                else {}
            )
            node_data.update({MCYEAR_COL: [path_parts[MC_YEAR_INDEX]] * len(matrix[0])})
            node_data.update({col: vals for col, vals in zip(columns, matrix) if col in kept_columns})

            df = pd.DataFrame(node_data)
            final_df = df if final_df is None else pd.concat([final_df, df], ignore_index=True)  # type: ignore

        return {} if final_df is None else final_df.fillna("N/A").to_dict(orient="list")  # type: ignore

    def get_study_sim_result(
        self,
        study: T,
    ) -> t.List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data
        """
        study_data = self.get_raw(study)
        patch_metadata = self.patch_service.get(study)
        results: t.List[StudySimResultDTO] = []
        if study_data.config.outputs is not None:
            reference = (patch_metadata.outputs or PatchOutputs()).reference
            for output in study_data.config.outputs:
                output_data: Simulation = study_data.config.outputs[output]
                try:
                    file_metadata = FileStudyHelpers.get_config(study_data, output_data.get_file())
                    settings = StudySimSettingsDTO(
                        general=file_metadata["general"],
                        input=file_metadata["input"],
                        output=file_metadata["output"],
                        optimization=file_metadata["optimization"],
                        otherPreferences=file_metadata["other preferences"],
                        advancedParameters=file_metadata["advanced parameters"],
                        seedsMersenneTwister=file_metadata["seeds - Mersenne Twister"],
                        playlist=[year for year in (get_playlist(file_metadata) or {}).keys()],
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
        output: t.Union[t.BinaryIO, Path],
        output_name: t.Optional[str] = None,
    ) -> t.Optional[str]:
        """
        Import additional output in an existing study.

        Args:
            metadata: study
            output: new output (path or zipped data)
            output_name: optional suffix name to append to output name

        Returns:
            Output identifier.

        Raises:
            BadArchiveContent: If the output archive is corrupted or in an unknown format.
        """
        path_output = Path(metadata.path) / "output" / f"imported_output_{str(uuid4())}"
        study_id = metadata.id
        path_output.mkdir(parents=True)
        output_full_name: t.Optional[str]
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

            stopwatch.log_elapsed(lambda t: logger.info(f"Copied output for {study_id} in {t}s"))
            fix_study_root(path_output)
            output_full_name = extract_output_name(path_output, output_name)
            extension = ".zip" if is_zipped else ""
            path_output = path_output.rename(Path(path_output.parent, output_full_name + extension))

            data = self.get(metadata, f"output/{output_full_name}", 1, use_cache=False)

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

    def export_study(self, metadata: T, target: Path, outputs: bool = True) -> Path:
        """
        Export and compress the study inside a ZIP file.

        Args:
            metadata: Study metadata object.
            target: Path of the file to export to.
            outputs: Flag to indicate whether to include the output folder inside the exportation.

        Returns:
            The ZIP file containing the study files compressed inside.
        """
        path_study = Path(metadata.path)
        with tempfile.TemporaryDirectory(dir=self.config.storage.tmp_dir) as tmpdir:
            logger.info(f"Exporting study {metadata.id} to temporary path {tmpdir}")
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(metadata, tmp_study_path, outputs)
            stopwatch = StopWatch()
            zip_dir(tmp_study_path, target)
            stopwatch.log_elapsed(lambda x: logger.info(f"Study {path_study} exported (zipped mode) in {x}s"))
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
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} from study {metadata.path} exported in {x}s"))

    def _read_additional_data_from_files(self, file_study: FileStudy) -> StudyAdditionalData:
        logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        author = file_study.tree.get(url=["study", "antares", "author"])
        patch = self.patch_service.get_from_filestudy(file_study)
        study_additional_data = StudyAdditionalData(horizon=horizon, author=author, patch=patch.json())
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

    def unarchive_study_output(self, study: T, output_id: str, keep_src_zip: bool) -> bool:
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
