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
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import (
    ChildNotFoundError,
    OutputAlreadyArchived,
    OutputAlreadyExists,
    OutputAlreadyUnarchived,
    OutputNotFound,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.utils.archives import (
    ArchiveFormat,
    archive_dir,
    extract_archive_from_path,
    extract_archive_from_stream,
    is_zip,
    unzip,
)
from antarest.core.utils.utils import StopWatch
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.output.filestudy.aggregator_management import AggregatorManager
from antarest.output.filestudy.file_output_utils import extract_variables_list
from antarest.output.filestudy.utils import QueryFileType
from antarest.output.model import OutputVariablesList
from antarest.output.storage.file.repository import FileOutputRepository
from antarest.output.storage.output_storage import (
    IOutputStorage,
    OutputDetails,
    OutputMetadata,
    OutputSettings,
    OutputStorageType,
)
from antarest.study.model import (
    MatrixFrequency,
    MatrixIndex,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import get_playlist, parse_outputs
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import (
    extract_output_name,
    fix_study_root,
    get_disk_usage,
    get_start_date,
    remove_from_cache,
)
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileStudyOutputs:
    """
    The implementation based on outputs stored as files requires the following information to work with a study.

    Attributes:
        get_file_study: allows to load the underlying file study as needed.
        outputs_path: path to the study outputs directory.
        is_managed: Whether the outputs are managed by the AntaresWeb server or not.
    """

    get_file_study: Callable[[], FileStudy]
    outputs_path: Path
    is_managed: bool


class IFileOutputsProvider(ABC):
    """
    Responsible for mapping study ID to file output information.
    """

    @abstractmethod
    def get_outputs(self, study_id: str) -> FileStudyOutputs: ...


def _output_path(outputs_root: Path, output_name: str) -> Path:
    """
    Path for an unarchived output.
    """
    return outputs_root / output_name


def _archived_output_path(outputs_root: Path, output_name: str) -> Path:
    """
    Path for an archived output. Only zip is currently supported.
    """
    return outputs_root / f"{output_name}{ArchiveFormat.ZIP}"


def _output_paths(outputs_root: Path, output_name: str) -> tuple[Path, Path]:
    """
    Returns (output_path, archived_output_path) for convenience.
    """
    return _output_path(outputs_root, output_name), _archived_output_path(outputs_root, output_name)


def _find_archived_output(outputs_root: Path, output_name: str) -> Path | None:
    possible_path = _archived_output_path(outputs_root, output_name)
    return possible_path if possible_path.exists() else None


def _copy_output(src_outputs_root: Path, output_id: str, dest_outputs_root: Path) -> None:
    """
    Copies one output from one "outputs" dir to another, keeping the archived state unchanged.
    """
    src_folder = _output_path(src_outputs_root, output_id)

    if _output_exists(dest_outputs_root, output_id):
        raise OutputAlreadyExists(output_id)

    if src_folder.exists():
        shutil.copytree(src_folder, _output_path(dest_outputs_root, output_id))
    elif archive_path := _find_archived_output(src_outputs_root, output_id):
        # The src output could be archived
        dest_outputs_root.mkdir(exist_ok=True)
        shutil.copy(archive_path, dest_outputs_root)
    else:
        raise OutputNotFound(output_id)


def _is_output_archived(outputs_root: Path, output_id: str) -> bool:
    output_path = _output_path(outputs_root, output_id)
    if output_path.is_dir():
        return False
    archive_path = _archived_output_path(outputs_root, output_id)
    if archive_path.is_file():
        return True
    raise OutputNotFound(output_id)


def _output_exists(outputs_root: Path, output_id: str) -> bool:
    return _output_path(outputs_root, output_id).is_dir() or _archived_output_path(outputs_root, output_id).is_file()


def _import_zip_as_archived(
    study_id: str, output_zip_path: Path, study_outputs_path: Path, output_name_suffix: str | None, logs: SimulationLogs
) -> str:
    """Simply copies the zip to destination study/output/<output_name>.zip, with the right name extracted from output
    files."""
    t = StopWatch()

    output_full_name = extract_output_name(output_zip_path, output_name_suffix)
    final_path = _archived_output_path(study_outputs_path, output_full_name)
    study_outputs_path.mkdir(exist_ok=True)
    shutil.copyfile(output_zip_path, final_path)

    _add_logs(final_path, logs)

    logger.info(f"Copied output for {study_id} in {t}s")
    return output_full_name


def _copy_file(src: Path, dst_root: Path, dst: PurePosixPath) -> None:
    """
    Copies src to dst inside dst_root, dst_root being either a plain directory, or a zip file.
    """
    if is_zip(dst_root):
        with zipfile.ZipFile(dst_root, mode="a") as zf:
            zf.write(src, str(dst))
    else:
        shutil.copyfile(src, dst_root / dst)


def _add_logs(output_dir: Path, logs: SimulationLogs) -> None:
    if logs.out:
        _copy_file(logs.out, output_dir, PurePosixPath("antares-out.log"))
    if logs.err:
        _copy_file(logs.err, output_dir, PurePosixPath("antares-err.log"))


class InStudyFileOutputStorage(IOutputStorage):
    """
    Implementation based on outputs stored in antares-solver file format, inside a study.
    """

    def __init__(
        self,
        outputs_provider: IFileOutputsProvider,
        cache: ICache,
        remote_executor: IRemoteExecutor,
        repository: FileOutputRepository,
    ) -> None:
        self._outputs_provider = outputs_provider
        self._cache = cache
        self._remote_executor = remote_executor
        self._repository = repository

    @override
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.IN_STUDY_FILE_TREE

    @override
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name_suffix: str | None = None,
        logs: SimulationLogs = SimulationLogs.no_logs(),
    ) -> str:
        """
        Starts by creating a temporary output directory inside the output dir, then copies the provided output into it.

        Finally rename the temp directory to the actual output name.

        In case of a zip path, seems that it's just copied, not extracted. Why that difference in logic ?
        Probably because for external studies, we only want to unarchive it afterwards, at the service level...
        But it's far too implicit !
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        # Optimized path to copy outputs on external devices. Will then be unarchived there.
        if isinstance(output, Path) and is_zip(output):
            output_name = _import_zip_as_archived(
                study_id, output, study_outputs.outputs_path, output_name_suffix, logs
            )
            remove_from_cache(self._cache, study_id)
            return output_name

        # Output is first written to a temporary directory which is then moved to the actual output path
        tmp_output_dir = study_outputs.outputs_path / f"imported_output_{str(uuid4())}"
        try:
            if isinstance(output, Path):
                t = StopWatch()
                shutil.copytree(output, tmp_output_dir)
                logger.info(f"Copied output for {study_id} in {t}s")
            else:
                # in case of stream, it's assumed to be an archive which we extract to the temporary output directory
                t = StopWatch()
                extract_archive_from_stream(output, tmp_output_dir)
                fix_study_root(tmp_output_dir)
                logger.info(f"Extracted output for {study_id} in {t}s")

            # Add log files
            _add_logs(tmp_output_dir, logs)

            # Moving temporary directory to actual directory
            output_name = extract_output_name(tmp_output_dir, output_name_suffix)
            tmp_output_dir.rename(_output_path(study_outputs.outputs_path, output_name))

            remove_from_cache(self._cache, study_id)

            return output_name
        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(tmp_output_dir, ignore_errors=True)
            raise

    @override
    def get_output_details(self, study_id: str, output_id: str) -> OutputDetails:
        """
        Get the list of output for a study.
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)
        outputs = study_outputs.get_file_study().config.outputs
        if output_id not in outputs:
            raise OutputNotFound(output_id)
        output_data: Simulation = outputs[output_id]

        study_data = study_outputs.get_file_study()
        file_metadata = FileStudyHelpers.get_config(study_data, output_data.get_file())
        settings = OutputSettings(
            general=file_metadata["general"],
            optimization=file_metadata["optimization"],
            playlist=[year for year in (get_playlist(file_metadata) or {}).keys()],
        )

        return OutputDetails(
            name=output_id,
            mode=output_data.mode,
            synthesis=output_data.synthesis,
            by_year=output_data.by_year,
            nb_years=output_data.nbyears,
            archived=output_data.archived,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
            settings=settings,
        )

    @override
    def list_outputs(self, study_id: str) -> list[OutputMetadata]:
        """
        Get the list of output for a study.
        """
        outputs_path = self._outputs_provider.get_outputs(study_id).outputs_path
        simulations = parse_outputs(outputs_path)
        return [
            OutputMetadata(id=output_id, in_study=True, archived=output.archived)
            for output_id, output in simulations.items()
        ]

    @override
    def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:
        src_outputs_dir = self._outputs_provider.get_outputs(src_study_id).outputs_path
        target_outputs_dir = self._outputs_provider.get_outputs(target_study_id).outputs_path
        _copy_output(src_outputs_dir, output_id, target_outputs_dir)
        remove_from_cache(self._cache, target_study_id)

    @override
    def delete_output(self, study_id: str, output_id: str) -> None:
        """
        Delete a simulation output
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        if not _output_exists(study_outputs.outputs_path, output_id):
            raise OutputNotFound(output_id)

        output_path, archived_output_path = _output_paths(study_outputs.outputs_path, output_id)
        if output_path.exists() and output_path.is_dir():
            shutil.rmtree(output_path, ignore_errors=True)
        if archived_output_path.exists():
            archived_output_path.unlink()

        remove_from_cache(self._cache, study_id)

    @override
    def write_output_to_dir(self, study_id: str, output_id: str, parent: Path) -> None:
        """
        Writes outputs in filestudy format into parent directory
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        if not _output_exists(study_outputs.outputs_path, output_id):
            raise OutputNotFound(output_id)

        output_path, archived_output_path = _output_paths(study_outputs.outputs_path, output_id)
        if output_path.is_dir():
            shutil.copytree(output_path, parent / output_id, dirs_exist_ok=False)
        elif archived_output_path.is_file():
            extract_archive_from_path(archived_output_path, parent / output_id)

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            study_id: study id
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        logger.info(f"Exporting output {output_id} from study {study_id}")

        if not _output_exists(study_outputs.outputs_path, output_id):
            raise OutputNotFound(output_id)

        output_path, archived_output_path = _output_paths(study_outputs.outputs_path, output_id)

        if archived_output_path.exists():
            shutil.copyfile(archived_output_path, target)
            return

        stopwatch = StopWatch()
        archive_dir(output_path, target, archive_format=ArchiveFormat.ZIP)
        logger.info(f"Output {output_id} from study {study_id} exported in {stopwatch}s")

    @override
    def output_exists(self, study_id: str, output_id: str) -> bool:
        """Check if a study output exists."""
        study_outputs = self._outputs_provider.get_outputs(study_id)
        return _output_exists(study_outputs.outputs_path, output_id)

    @override
    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        """Check if a study output is archived."""
        study_outputs = self._outputs_provider.get_outputs(study_id)
        return _is_output_archived(study_outputs.outputs_path, output_id)

    @override
    def archive_study_output(self, study_id: str, output_id: str) -> None:
        """Archive a study output."""
        study_outputs = self._outputs_provider.get_outputs(study_id)
        if _is_output_archived(study_outputs.outputs_path, output_id):
            raise OutputAlreadyArchived(output_id)

        output_path, archived_output_path = _output_paths(study_outputs.outputs_path, output_id)
        # If exists, we assume it's a valid archive.
        if not archived_output_path.is_file():
            archive_dir(
                output_path,
                archived_output_path,
                archive_format=ArchiveFormat.ZIP,
            )
        shutil.rmtree(output_path)

        remove_from_cache(self._cache, study_id)

    def _remote_unarchive(self, output_id: str, study_outputs: FileStudyOutputs) -> None:
        dest, src = _output_paths(study_outputs.outputs_path, output_id)
        self._remote_executor.execute_remote_task(
            f"unarchive_{output_id}",
            ArchiveTaskArgs(src=str(src), dest=str(dest)).model_dump(mode="json"),
        )

    # noinspection SpellCheckingInspection
    @override
    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        """Un-archive a study output."""
        study_outputs = self._outputs_provider.get_outputs(study_id)

        if not _is_output_archived(study_outputs.outputs_path, output_id):
            raise OutputAlreadyUnarchived(output_id)

        # Specific logic for "external" workspaces: we ask for unarchiving to the remote executor ...
        if not study_outputs.is_managed:
            self._remote_unarchive(output_id, study_outputs)
            remove_from_cache(self._cache, study_id)
        else:
            study_outputs = self._outputs_provider.get_outputs(study_id)
            output_path, archived_output_path = _output_paths(study_outputs.outputs_path, output_id)
            try:
                # Note: here we don't remove the archived version, allows to speed up a subsequent archival,
                #       but at some disk usage cost for unarchived studies.
                unzip(output_path, archived_output_path)
                remove_from_cache(self._cache, study_id)
            except Exception as e:
                logger.warning(
                    f"Failed to unarchive study {study_id} output {output_id}",
                    exc_info=e,
                )
                if output_path.exists() and output_path.is_dir():
                    shutil.rmtree(output_path, ignore_errors=True)
                raise

    @override
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        """
        Digest of the output.
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)
        file_study = study_outputs.get_file_study()
        digest_node = file_study.tree.get_node(url=["output", output_id, "economy", "mc-all", "grid", "digest"])
        assert isinstance(digest_node, DigestSynthesis)
        return digest_node.get_ui()

    @override
    def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
        """
        Get the time index (start date and step count) for output matrices with a given frequency.
        Args:
            study_id: ID of the study
            output_id: ID of the output
            frequency: temporal frequency (hourly, daily, weekly, monthly, annually)
        Returns:
            MatrixIndex with start_date, steps, first_week_size and level
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)
        file_study = study_outputs.get_file_study()
        return get_start_date(file_study, output_id, frequency)

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
        study_outputs = self._outputs_provider.get_outputs(study_id)
        aggregator_manager = AggregatorManager(
            _output_path(study_outputs.outputs_path, output_id),
            query_file,
            frequency,
            ids_to_consider,
            columns_names,
            transform_columns_headers,
            mc_years,
        )
        return aggregator_manager.aggregate_output_data()

    @override
    def get_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        study_outputs = self._outputs_provider.get_outputs(study_id)

        output_variables = self._repository.get_output_variables_list(study_id, output_id)
        if output_variables:
            return output_variables

        # Fetches the data from stored output
        output_dir = _output_path(study_outputs.outputs_path, output_id)
        model = extract_variables_list(output_dir)

        # Save the model inside DB for next calls
        self._repository.save_output_variables_list(study_id, output_id, model)

        return model

    @override
    def get_logs(self, study_id: str, output_id: str, log_type: LogType) -> str:
        output_path = self._outputs_provider.get_outputs(study_id).outputs_path

        log_locations = {
            LogType.STDOUT: [Path(output_id) / "antares-out.log", Path(output_id) / "simulation.log"],
            LogType.STDERR: [Path(output_id) / "antares-err.log"],
        }
        empty_log = False
        for log_location in log_locations[log_type]:
            try:
                # Assume UTF-8 but ignore errors, it's difficult to be sure of log encoding
                # especially because of windows error messages
                file_path = output_path / log_location
                return file_path.read_text(encoding="utf-8", errors="replace")
            except FileNotFoundError:
                empty_log = True
                pass
        if empty_log:
            return ""
        raise ChildNotFoundError(f"Logs for {output_id} of study {study_id} were not found")

    @override
    def get_disk_usage(self, study_id: str, output_id: str) -> int:
        study_outputs = self._outputs_provider.get_outputs(study_id)
        output_dir = _output_path(study_outputs.outputs_path, output_id)
        return get_disk_usage(output_dir)
