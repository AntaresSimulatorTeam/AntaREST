# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import logging
import shutil
import tempfile
import uuid
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import BinaryIO

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import (
    OutputAggregationError,
    OutputAlreadyExists,
    OutputNotFound,
    ShouldNotHappenException,
)
from antarest.core.serde.ini_reader import IniReader
from antarest.core.utils.archives import (
    ArchiveFormat,
    archive_dir,
    extract_archive_from_path,
    extract_archive_from_stream,
)
from antarest.core.utils.sqlalchemy import clone_orm_object
from antarest.core.utils.utils import StopWatch
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.lfs.lfs import ILargeFileStorage
from antarest.output.filestudy.file_output_utils import (
    extract_output_details,
    extract_variables_list,
    find_simulation_log,
)
from antarest.output.filestudy.utils import QueryFileType
from antarest.output.model import OutputVariablesList
from antarest.output.storage.output_storage import (
    IOutputStorage,
    OutputDetails,
    OutputMetadata,
    OutputStorageType,
)
from antarest.output.storage.v2.repository import (
    DbOutputMetadataV2,
    OutputV2Repository,
)
from antarest.output.storage.v2.variables_storage import (
    extract_output_to_parquet,
    parquet_output_dir,
    read_output_from_parquet,
)
from antarest.study.business.model.config.general_model import Mode
from antarest.study.model import MatrixFrequency, MatrixIndex
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI
from antarest.study.storage.utils import (
    SimulationRangeDefinition,
    extract_output_name,
    fix_study_root,
    get_disk_usage,
    get_matrix_index,
    parse_simulation_range,
)

logger = logging.getLogger(__name__)


def _archive_id(study_id: str, output_name: str) -> str:
    # TODO: use a UUID stored in DB instead ?
    return f"{study_id}-{output_name}"


def _write_temporary_files(tmp_dir: Path, output: BinaryIO | Path) -> tuple[Path, Path]:
    """
    Ensures we have the output in both forms on disk, compressed and uncompressed,
    whatever the input is (a compressed binary stream, or a compressed or uncompressed path).

    Returns:
        the path to the compressed archive, and the path to the uncompressed directory.
    """
    archive_path = tmp_dir / f"{uuid.uuid4()}.zip"
    dir_path = tmp_dir / f"{uuid.uuid4()}"
    try:
        if isinstance(output, Path):
            if output.is_dir():
                shutil.copytree(output, dir_path, dirs_exist_ok=False)
                archive_path = tmp_dir / f"{uuid.uuid4()}{ArchiveFormat.ZIP}"
                archive_dir(dir_path, archive_path, remove_source_dir=False, archive_format=ArchiveFormat.ZIP)
            else:
                shutil.copy(output, archive_path)
                with archive_path.open("rb") as f:
                    extract_archive_from_stream(f, dir_path)
        else:
            # write the archive to one dir and extract to the second
            with archive_path.open("wb") as f:
                shutil.copyfileobj(output, f)
            with archive_path.open("rb") as f:
                extract_archive_from_stream(f, dir_path)

        # Still needed to ensure the output is not in a sub-directory
        fix_study_root(dir_path)
        # TODO: optimize this, we should not do it when not needed (when the layout was OK)
        archive_path.unlink()
        archive_dir(dir_path, archive_path, remove_source_dir=False, archive_format=ArchiveFormat.ZIP)

    except Exception:
        shutil.rmtree(archive_path, ignore_errors=True)
        shutil.rmtree(dir_path, ignore_errors=True)
        raise
    return archive_path, dir_path


def _extract_simulation_range(output_dir: Path) -> SimulationRangeDefinition:
    parameters_path = output_dir / "about-the-study" / "parameters.ini"
    parameters = IniReader().read(parameters_path)
    return parse_simulation_range(parameters["general"])


def _db_metadata_to_simulation_range(metadata: DbOutputMetadataV2) -> SimulationRangeDefinition:
    return SimulationRangeDefinition(
        starting_month=metadata.start_month,
        january_1st_weekday=metadata.january_first_weekday,
        leap_year=metadata.leap_year,
        start_day=metadata.start_day,
        end_day=metadata.end_day,
        first_weekday=metadata.first_weekday,
    )


def _db_metadata_to_details(metadata: DbOutputMetadataV2) -> OutputDetails:
    return OutputDetails(
        name=metadata.output_name,
        mode=Mode(metadata.mode),
        synthesis=metadata.synthesis,
        by_year=metadata.by_year,
        nb_years=metadata.nb_years,
        archived=metadata.archived,
        storage_type=OutputStorageType.V2,
    )


class V2OutputStorage(IOutputStorage):
    """
    The implementation will be based on a few sub-components:
    - archives will be stored in an LFS
    - metadata will be stored in database
    - actual variables values will be unarchived to parquet files

    The tmp directory will be used on import or unarchival to store uncompressed files.
    """

    def __init__(
        self,
        tmp_dir: Path,
        repository: OutputV2Repository,
        archive_storage: ILargeFileStorage,
        variables_dir: Path,
    ) -> None:
        self._archive_storage = archive_storage
        self._repository = repository
        self._tmp_dir = tmp_dir
        self._variables_dir = variables_dir

    def _get_metadata(self, study_id: str, output_name: str) -> DbOutputMetadataV2 | None:
        return self._repository.get_output_metadata(study_id, output_name)

    def _require_metadata(self, study_id: str, output_name: str) -> DbOutputMetadataV2:
        metadata = self._repository.get_output_metadata(study_id, output_name)
        if metadata is None:
            raise OutputNotFound(f"Output {output_name} does not exist.")
        return metadata

    @override
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.V2

    @override
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name_suffix: str | None = None,
        logs: SimulationLogs = SimulationLogs.no_logs(),
    ) -> str:
        logger.info(f"Importing output for study {study_id} to internal storage.")
        timer = StopWatch()
        tmp_dir = self._tmp_dir / f"output-import-{study_id}-{uuid.uuid4()}"
        tmp_dir.mkdir(parents=True)
        try:
            # We first ensure we have 2 versions of the output: as an archive, and as a directory
            archive_path, dir_path = _write_temporary_files(tmp_dir, output)
            output_name = extract_output_name(dir_path, output_name_suffix)

            if self._get_metadata(study_id, output_name) is not None:
                raise OutputAlreadyExists(output_name)

            # Write the compressed version to archive storage
            self._archive_storage.write_file(_archive_id(study_id, output_name), archive_path)

            # Create metadata
            output_details = extract_output_details(dir_path)

            simulation_range = _extract_simulation_range(dir_path)

            variables_target = parquet_output_dir(self._variables_dir, study_id, output_name)
            extract_output_to_parquet(dir_path, variables_target)

            self._repository.save_output_metadata(
                DbOutputMetadataV2(
                    study_id=study_id,
                    output_name=output_name,
                    archived=False,
                    mode=output_details.mode,
                    synthesis=output_details.synthesis,
                    by_year=output_details.by_year,
                    nb_years=output_details.nb_years,
                    start_month=simulation_range.starting_month,
                    january_first_weekday=simulation_range.january_1st_weekday,
                    leap_year=simulation_range.leap_year,
                    start_day=simulation_range.start_day,
                    end_day=simulation_range.end_day,
                    first_weekday=simulation_range.first_weekday,
                )
            )

            self._save_logs(study_id, output_name, logs, dir_path)

            variables_list = extract_variables_list(dir_path)
            self._repository.save_output_variables_list(study_id, output_name, variables_list)

            logger.info(f"Output imported to internal storage in {timer}s.")
            return output_name
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _save_logs(self, study_id: str, output_id: str, logs: SimulationLogs, output_dir: Path) -> None:
        out_log = logs.out or find_simulation_log(output_dir, LogType.STDOUT)
        if out_log:
            log_content = out_log.read_text(encoding="utf-8")
            self._repository.save_log(study_id, output_id, LogType.STDOUT, log_content)
        err_log = logs.err or find_simulation_log(output_dir, LogType.STDERR)
        if err_log:
            log_content = err_log.read_text(encoding="utf-8")
            self._repository.save_log(study_id, output_id, LogType.STDERR, log_content)

    @override
    def list_outputs(self, study_id: str) -> list[OutputMetadata]:
        return [
            OutputMetadata(id=o.output_name, in_study=False, archived=o.archived)
            for o in self._repository.search_output_metadata(study_id)
        ]

    @override
    def get_output_details(self, study_id: str) -> list[OutputDetails]:
        """
        Get the list of output for a study.
        """
        result = []
        for output_metadata in self._repository.search_output_metadata(study_id):
            result.append(_db_metadata_to_details(output_metadata))
        return result

    @override
    def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:

        if self._get_metadata(target_study_id, output_id) is not None:
            raise OutputAlreadyExists(output_id)

        with tempfile.TemporaryDirectory(dir=self._tmp_dir) as tmp_dir:
            tmp_archive_path = Path(tmp_dir) / "output.zip"
            self._archive_storage.read_file(_archive_id(src_study_id, output_id), tmp_archive_path)
            self._archive_storage.write_file(_archive_id(target_study_id, output_id), tmp_archive_path)

        metadata = self._require_metadata(src_study_id, output_id)
        copy_metadata = clone_orm_object(DbOutputMetadataV2, metadata)
        copy_metadata.study_id = target_study_id
        copy_metadata.output_name = output_id
        self._repository.save_output_metadata(copy_metadata)

        out_log = self._repository.get_log(src_study_id, output_id, LogType.STDOUT)
        err_log = self._repository.get_log(src_study_id, output_id, LogType.STDERR)
        self._repository.save_log(target_study_id, output_id, LogType.STDOUT, out_log)
        self._repository.save_log(target_study_id, output_id, LogType.STDERR, err_log)

        variables_list = self._repository.get_output_variables_list(src_study_id, output_id)
        if variables_list is None:
            raise ShouldNotHappenException(f"Variables list not found for output {src_study_id}/{output_id}.")
        self._repository.save_output_variables_list(target_study_id, output_id, variables_list)

        src_vars = parquet_output_dir(self._variables_dir, src_study_id, output_id)
        dst_vars = parquet_output_dir(self._variables_dir, target_study_id, output_id)
        if src_vars.exists():
            shutil.copytree(src_vars, dst_vars)

    @override
    def delete_output(self, study_id: str, output_id: str) -> None:
        # TODO: we should have some sort of async behaviour so that
        #       the output appears deleted asap.
        #       Maybe only mark it deleted, and have it removed in the background.
        logger.info(f"Deleting output {study_id}/{output_id} from internal storage.")
        self._require_metadata(study_id, output_id)
        self._archive_storage.delete_file(_archive_id(study_id, output_id))
        shutil.rmtree(parquet_output_dir(self._variables_dir, study_id, output_id), ignore_errors=True)
        self._repository.delete_output(study_id, output_id)

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        logger.info(f"Exporting output {study_id}/{output_id} from internal storage.")
        self._require_metadata(study_id, output_id)
        self._archive_storage.read_file(_archive_id(study_id, output_id), target)

    @override
    def output_exists(self, study_id: str, output_id: str) -> bool:
        return self._get_metadata(study_id, output_id) is not None

    @override
    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        metadata = self._require_metadata(study_id, output_id)
        return metadata.archived

    @override
    def archive_study_output(self, study_id: str, output_id: str) -> None:
        logger.info(f"Archiving output {study_id}/{output_id} in internal storage.")
        metadata = self._require_metadata(study_id, output_id)
        metadata.archived = True
        self._repository.save_output_metadata(metadata)

        # Delete the parquet directory to free disk space
        variables_target = parquet_output_dir(self._variables_dir, study_id, output_id)
        shutil.rmtree(variables_target, ignore_errors=True)

    @override
    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        logger.info(f"Unarchiving output {study_id}/{output_id} in internal storage.")
        metadata = self._require_metadata(study_id, output_id)

        # Rebuild parquet files from the archive BEFORE updating metadata,
        # so that if reconstruction fails, the output stays marked as archived.
        with tempfile.TemporaryDirectory(dir=self._tmp_dir) as tmp_dir:
            tmp_archive_path = Path(tmp_dir) / "output.zip"
            self._archive_storage.read_file(_archive_id(study_id, output_id), tmp_archive_path)
            dir_path = Path(tmp_dir) / "output"
            extract_archive_from_path(tmp_archive_path, dir_path)
            variables_target = parquet_output_dir(self._variables_dir, study_id, output_id)
            extract_output_to_parquet(dir_path, variables_target)

        metadata.archived = False
        self._repository.save_output_metadata(metadata)

    @override
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        # TODO: at import time, extract and dave either as file or in DB
        raise NotImplementedError()

    @override
    def get_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        """
        Get variables list of this output.
        """
        result = self._repository.get_output_variables_list(study_id, output_id)
        if not result:
            raise ValueError(f"Variables list not found for output {study_id}/{output_id}.")
        return result

    @override
    def write_output_to_dir(self, study_id: str, output_id: str, parent: Path) -> None:
        with tempfile.TemporaryDirectory(dir=self._tmp_dir) as tmp_dir:
            tmp_archive_path = Path(tmp_dir) / "output.zip"
            self._archive_storage.read_file(_archive_id(study_id, output_id), tmp_archive_path)
            extract_archive_from_path(tmp_archive_path, parent / output_id)

    @override
    def get_logs(self, study_id: str, output_id: str, log_type: LogType) -> str:
        return self._repository.get_log(study_id, output_id, log_type)

    @override
    def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
        metadata = self._require_metadata(study_id, output_id)
        simulation_range = _db_metadata_to_simulation_range(metadata)
        return get_matrix_index(simulation_range, is_output=True, level=frequency)

    @override
    def aggregate_output_data(
        self,
        study_id: str,
        output_id: str,
        query_file: QueryFileType,
        frequency: MatrixFrequency,
        ids_to_consider: Sequence[str],
        columns_names: Sequence[str],
        transform_columns_headers: bool,
        mc_years: Sequence[int] | None = None,
    ) -> Iterator[pl.DataFrame]:
        target_dir = parquet_output_dir(self._variables_dir, study_id, output_id)
        has_data = False
        for batch in read_output_from_parquet(
            target_dir, query_file, frequency, ids_to_consider, columns_names, mc_years
        ):
            if batch.is_empty():
                continue
            has_data = True
            if not transform_columns_headers:
                batch = batch.drop("timeId", strict=False)
            yield batch

        if not has_data:
            raise OutputAggregationError(output_id, "No output data matching the criteria were found")

    @override
    def get_disk_usage(self, study_id: str, output_id: str) -> int:
        output_dir = parquet_output_dir(self._variables_dir, study_id, output_id)
        return get_disk_usage(output_dir)
