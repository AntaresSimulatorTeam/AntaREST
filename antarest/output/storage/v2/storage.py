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
from typing import Any, BinaryIO

import pandas as pd
import polars as pl
from sqlalchemy import delete, select
from typing_extensions import override

from antarest.core.exceptions import (
    OutputAggregationError,
    OutputAlreadyExists,
    OutputNotFound,
)
from antarest.core.serde.ini_reader import IniReader
from antarest.core.utils.archives import (
    ArchiveFormat,
    archive_dir,
    extract_archive_from_path,
    extract_archive_from_stream,
)
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sqlalchemy import clone_orm_object
from antarest.core.utils.utils import StopWatch
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.lfs.lfs import ILargeFileStorage
from antarest.output.filestudy.logs import find_simulation_log
from antarest.output.filestudy.metadata import (
    extract_output_details,
)
from antarest.output.filestudy.model import (
    FileOutput,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    QueryFileType,
)
from antarest.output.model import MatrixAggregationResultDTO, OutputVariablesList, StudyDownloadDTO
from antarest.output.model.download import MatrixIndex
from antarest.output.storage.output_storage import (
    IOutputStorage,
    OutputDetails,
    OutputMetadata,
    OutputStorageType,
)
from antarest.output.storage.v2.dbmodel import ELEMENT_TABLES, DbParquetVariable, ElementType, ScenarioAggregation
from antarest.output.storage.v2.download import build_matrix_aggregation_result
from antarest.output.storage.v2.iteration import aggregate_data
from antarest.output.storage.v2.layout import FILE_TYPES
from antarest.output.storage.v2.metadata import ParquetOutputMetadata
from antarest.output.storage.v2.repository import (
    DbOutputMetadataV2,
    OutputV2Repository,
)
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import (
    create_parquet_files,
    parquet_output_dir,
)
from antarest.study.business.model.config.general_model import Mode
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
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
        id=metadata.output_name,
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
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

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
    def import_outputs(self, study_id: str, src_outputs_dir: Path) -> None:
        for output in src_outputs_dir.iterdir():
            self.import_output(study_id, output)

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
        written_output: str | None = None
        try:
            # We first ensure we have 2 versions of the output: as an archive, and as a directory
            archive_path, dir_path = _write_temporary_files(tmp_dir, output)
            output_name = extract_output_name(dir_path, output_name_suffix)

            if self._get_metadata(study_id, output_name) is not None:
                raise OutputAlreadyExists(output_name)

            # Write the compressed version to archive storage
            written_output = output_name
            self._archive_storage.write_file(_archive_id(study_id, output_name), archive_path)

            # Create metadata
            output_details = extract_output_details(dir_path)

            simulation_range = _extract_simulation_range(dir_path)

            metadata = DbOutputMetadataV2(
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
            file_output = FileOutput(dir_path)
            metadata.mc_years = file_output.mc_years
            metadata.metadata_version = 1
            db.session.add(metadata)
            db.session.flush()
            extract_output_variables_to_database(db.session, metadata.id, file_output)
            variables_target = parquet_output_dir(self._variables_dir, study_id, output_name)
            create_parquet_files(ParquetOutputMetadata(db.session, metadata.id), file_output, variables_target)

            self._save_logs(study_id, output_name, logs, dir_path, commit=False)

            self._repository.save_output_metadata(metadata)

            logger.info(f"Output imported to internal storage in {timer}s.")
            return output_name
        except Exception:
            db.session.rollback()
            if written_output is not None:
                self._archive_storage.delete_file(_archive_id(study_id, written_output))
                shutil.rmtree(parquet_output_dir(self._variables_dir, study_id, written_output), ignore_errors=True)
            raise
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _save_logs(
        self, study_id: str, output_id: str, logs: SimulationLogs, output_dir: Path, *, commit: bool = True
    ) -> None:
        out_log = logs.out or find_simulation_log(output_dir, LogType.STDOUT)
        if out_log:
            log_content = out_log.read_text(encoding="utf-8")
            self._repository.save_log(study_id, output_id, LogType.STDOUT, log_content, commit=commit)
        err_log = logs.err or find_simulation_log(output_dir, LogType.STDERR)
        if err_log:
            log_content = err_log.read_text(encoding="utf-8")
            self._repository.save_log(study_id, output_id, LogType.STDERR, log_content, commit=commit)

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

        metadata = self._ensure_metadata(src_study_id, output_id)
        src_vars = parquet_output_dir(self._variables_dir, src_study_id, output_id)
        dst_vars = parquet_output_dir(self._variables_dir, target_study_id, output_id)
        try:
            with tempfile.TemporaryDirectory(dir=self._tmp_dir) as tmp_dir:
                tmp_archive_path = Path(tmp_dir) / "output.zip"
                self._archive_storage.read_file(_archive_id(src_study_id, output_id), tmp_archive_path)
                self._archive_storage.write_file(_archive_id(target_study_id, output_id), tmp_archive_path)

            copy_metadata = clone_orm_object(DbOutputMetadataV2, metadata)
            del copy_metadata.id
            copy_metadata.study_id = target_study_id
            db.session.add(copy_metadata)
            db.session.flush()
            for table in (DbParquetVariable, *ELEMENT_TABLES):
                for row in db.session.scalars(select(table).where(table.output_id == metadata.id)).all():
                    copied = type(row)(**{c.name: getattr(row, c.name) for c in row.__table__.columns})
                    setattr(copied, "output_id", copy_metadata.id)
                    db.session.add(copied)
            db.session.flush()
            for log_type in (LogType.STDOUT, LogType.STDERR):
                self._repository.save_log(
                    target_study_id,
                    output_id,
                    log_type,
                    self._repository.get_log(src_study_id, output_id, log_type),
                    commit=False,
                )
            if src_vars.exists():
                shutil.copytree(src_vars, dst_vars)
            db.session.commit()
        except Exception:
            db.session.rollback()
            self._archive_storage.delete_file(_archive_id(target_study_id, output_id))
            shutil.rmtree(dst_vars, ignore_errors=True)
            raise

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

        self._rebuild_metadata(metadata, unarchive=True)

    def _ensure_metadata(self, study_id: str, output_id: str) -> DbOutputMetadataV2:
        metadata = self._require_metadata(study_id, output_id)
        if metadata.metadata_version < 1:
            # Serialize upgrades of an existing output on PostgreSQL.
            metadata = db.session.execute(
                select(DbOutputMetadataV2)
                .where(DbOutputMetadataV2.id == metadata.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            ).scalar_one()
            if metadata.metadata_version < 1:
                self._rebuild_metadata(metadata)
        return metadata

    def _rebuild_metadata(self, metadata: DbOutputMetadataV2, unarchive: bool = False) -> None:
        """Reconstruct missing units/statistics from the archive, including legacy outputs.

        The old blob cannot supply this information. Keep the old parquet directory
        until replacement files are complete, and restore it if the DB commit fails.
        Archived outputs only need their headers until explicitly unarchived.
        """
        target = parquet_output_dir(self._variables_dir, metadata.study_id, metadata.output_name)
        backup = target.with_name(f"{target.name}.backup-{uuid.uuid4()}")
        replaced = False
        try:
            with tempfile.TemporaryDirectory(dir=self._tmp_dir) as tmp:
                archive = Path(tmp) / "output.zip"
                source = Path(tmp) / "output"
                self._archive_storage.read_file(_archive_id(metadata.study_id, metadata.output_name), archive)
                extract_archive_from_path(archive, source)
                fix_study_root(source)
                for table in (DbParquetVariable, *ELEMENT_TABLES):
                    db.session.execute(delete(table).where(table.output_id == metadata.id))
                file_output = FileOutput(source)
                metadata.mc_years = file_output.mc_years
                extract_output_variables_to_database(db.session, metadata.id, file_output)
                if unarchive or not metadata.archived:
                    self._variables_dir.mkdir(parents=True, exist_ok=True)
                    with tempfile.TemporaryDirectory(dir=self._variables_dir) as staging:
                        new_dir = Path(staging) / "parquet"
                        create_parquet_files(ParquetOutputMetadata(db.session, metadata.id), file_output, new_dir)
                        if target.exists():
                            target.rename(backup)
                        new_dir.rename(target)
                        replaced = True
                metadata.metadata_version = 1
                if unarchive:
                    metadata.archived = False
                db.session.commit()
        except Exception:
            db.session.rollback()
            if replaced:
                shutil.rmtree(target, ignore_errors=True)
            if backup.exists():
                backup.rename(target)
            raise
        finally:
            shutil.rmtree(backup, ignore_errors=True)

    @override
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        # TODO: at import time, extract and dave either as file or in DB
        raise NotImplementedError()

    @override
    def get_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        """
        Get variables list of this output.
        """
        metadata = self._ensure_metadata(study_id, output_id)
        return ParquetOutputMetadata(db.session, metadata.id).get_variables_list()

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
        mc_years: Sequence[int] | None = None,
    ) -> Iterator[pl.DataFrame]:
        metadata = self._ensure_metadata(study_id, output_id)
        if metadata.archived:
            raise OutputAggregationError(output_id, "Output is archived")
        aggregation: ScenarioAggregation = (
            "mc-ind" if isinstance(query_file, (MCIndAreasQueryFile, MCIndLinksQueryFile)) else "mc-all"
        )
        element_type: ElementType = FILE_TYPES[query_file.value]
        if isinstance(query_file, (MCIndLinksQueryFile, MCAllLinksQueryFile)):
            element_type = "link" if query_file.value == "values" else "link_id"
        has_data = False
        for batch in aggregate_data(
            ParquetOutputMetadata(db.session, metadata.id),
            parquet_output_dir(self._variables_dir, study_id, output_id),
            aggregation,
            element_type,
            frequency,
            mc_years or [],
            ids_to_consider,
            columns_names,
        ):
            has_data = True
            yield batch
        if not has_data:
            raise OutputAggregationError(output_id, "No output data matching the criteria were found")

    @override
    def get_disk_usage(self, study_id: str, output_id: str) -> int:
        output_dir = parquet_output_dir(self._variables_dir, study_id, output_id)
        return get_disk_usage(output_dir)

    @override
    def get_raw_content(self, study_id: str, output_id: str, url: list[str], formatted: bool) -> Any:
        # todo: implement this
        raise NotImplementedError()

    @override
    def get_matrix_as_dataframe(
        self, study_id: str, output_id: str, url: list[str], frequency: MatrixFrequency
    ) -> pd.DataFrame:
        # todo: implement this
        raise NotImplementedError()

    @override
    def get_original_file(self, study_id: str, output_id: str, url: list[str]) -> OriginalFile:
        # todo: implement this
        raise NotImplementedError()

    @override
    def get_matrix_aggregation_result(
        self, study_id: str, output_id: str, data_selection: StudyDownloadDTO
    ) -> MatrixAggregationResultDTO:
        metadata = self._ensure_metadata(study_id, output_id)
        if metadata.archived:
            raise OutputAggregationError(output_id, "Output is archived")
        parquet_metadata = ParquetOutputMetadata(db.session, metadata.id)
        output_dir = parquet_output_dir(self._variables_dir, study_id, output_id)
        return build_matrix_aggregation_result(parquet_metadata, output_dir, data_selection)
