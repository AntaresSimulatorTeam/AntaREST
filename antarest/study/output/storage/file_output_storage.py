# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Iterator, Optional, Sequence, cast
from uuid import uuid4

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import (
    BadOutputError,
    ChildNotFoundError,
    OutputAlreadyArchived,
    OutputAlreadyExists,
    OutputAlreadyUnarchived,
    OutputNotFound,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.utils.archives import ArchiveFormat, archive_dir, extract_archive, unarchive, unzip
from antarest.core.utils.utils import StopWatch
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    MatrixFrequency,
    MatrixIndex,
)
from antarest.study.output.aggregator_management import AggregatorManager
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.storage.output_storage import (
    IOutputStorage,
    OutputDetails,
    OutputMetadata,
    OutputStorageType,
)
from antarest.study.output.utils import QueryFileType
from antarest.study.output.variables_management import extract_variables_list
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)
from antarest.study.storage.utils import (
    extract_output_name,
    fix_study_root,
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
        study_workspace: name of the study workspace.
    """

    get_file_study: Callable[[], FileStudy]
    outputs_path: Path
    study_workspace: str


class IFileOutputsProvider(ABC):
    """
    Responsible for mapping study ID to file output information.
    """

    @abstractmethod
    def get_outputs(self, study_id: str) -> FileStudyOutputs: ...


def _find_archived_output(outputs_root: Path, output_name: str) -> Path | None:
    possible_paths = [outputs_root / f"{output_name}{ext}" for ext in ArchiveFormat]
    return next((path for path in possible_paths if path.exists()), None)


def _copy_output(src_outputs_root: Path, output_id: str, dest_outputs_root: Path) -> None:
    """
    Copies one output from one "outputs" dir to another, keeping the archived state unchanged.
    """
    src_folder = src_outputs_root / output_id

    if _output_exists(dest_outputs_root, output_id):
        raise OutputAlreadyExists(output_id)

    if src_folder.exists():
        shutil.copytree(src_folder, dest_outputs_root / output_id)
    elif archive_path := _find_archived_output(src_outputs_root, output_id):
        # The src output could be archived
        dest_outputs_root.mkdir(exist_ok=True)
        dest_path = dest_outputs_root
        shutil.copy(archive_path, dest_path)
    else:
        raise OutputNotFound(output_id)


def _is_output_archived(outputs_root: Path, output_id: str) -> bool:
    output_path = outputs_root / output_id
    if output_path.is_dir():
        return False
    zip_path = outputs_root / f"{output_id}{ArchiveFormat.ZIP}"
    if zip_path.is_file():
        return True
    raise OutputNotFound(output_id)


def _output_exists(outputs_root: Path, output_id: str) -> bool:
    output_path = outputs_root / output_id
    zip_path = outputs_root / f"{output_id}{ArchiveFormat.ZIP}"
    return output_path.is_dir() or zip_path.is_file()


class InStudyFileOutputStorage(IOutputStorage):
    """
    Implementation based on outputs stored in antares-solver file format, inside a study.
    """

    def __init__(self, outputs_provider: IFileOutputsProvider, cache: ICache, remote_executor: IRemoteExecutor) -> None:
        self._outputs_provider = outputs_provider
        self._cache = cache
        self._remote_executor = remote_executor

    @override
    @property
    def storage_type(self) -> OutputStorageType:
        return OutputStorageType.IN_STUDY_FILE_TREE

    @override
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name_suffix: Optional[str] = None,
    ) -> Optional[str]:
        study_outputs = self._outputs_provider.get_outputs(study_id)

        # Initialize to path to temporary output directory ?
        path_output = study_outputs.outputs_path / f"imported_output_{str(uuid4())}"

        path_output.mkdir(parents=True)
        output_full_name: Optional[str]
        is_zipped = False
        stopwatch = StopWatch()
        try:
            if isinstance(output, Path):
                if output.suffix != ArchiveFormat.ZIP:
                    shutil.copytree(output, path_output / "imported")
                elif output.suffix == ArchiveFormat.ZIP:
                    is_zipped = True
                    path_output.rmdir()
                    path_output = Path(str(path_output) + f"{ArchiveFormat.ZIP}")
                    shutil.copyfile(output, path_output)
            else:
                # in case of stream, we extract it to temporary output directory
                extract_archive(output, path_output)

            stopwatch.log_elapsed(lambda elapsed_time: logger.info(f"Copied output for {study_id} in {elapsed_time}s"))

            # Does nothing if zipped, else make sure that output files are just under that path, no nested directories.
            fix_study_root(path_output)
            output_full_name = extract_output_name(path_output, output_name_suffix)
            extension = f"{ArchiveFormat.ZIP}" if is_zipped else ""

            # Moving temporary directory to actual directory /output/<output-name>[.zip]
            path_output = path_output.rename(Path(path_output.parent, output_full_name + extension))
            remove_from_cache(self._cache, study_id)

            study_data = study_outputs.get_file_study()
            data = study_data.tree.get(["output", output_full_name], depth=1)

            if data is None:
                # TODO: what is that output id ??
                self.delete_output(study_id, "imported_output")
                raise BadOutputError("The output provided is not conform.")

        except Exception as e:
            logger.error("Failed to import output", exc_info=e)
            shutil.rmtree(path_output, ignore_errors=True)
            if is_zipped:
                Path(str(path_output) + f"{ArchiveFormat.ZIP}").unlink(missing_ok=True)
            raise

        return output_full_name

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
        return OutputDetails(
            name=output_id,
            mode=output_data.mode,
            synthesis=output_data.synthesis,
            by_year=output_data.by_year,
            nb_years=output_data.nbyears,
            archived=output_data.archived,
        )

    @override
    def list_outputs(self, study_id: str) -> list[OutputMetadata]:
        """
        Get the list of output for a study.
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)
        simulations = study_outputs.get_file_study().config.outputs
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
        output_path = study_outputs.outputs_path / output_id
        if output_path.exists() and output_path.is_dir():
            shutil.rmtree(output_path, ignore_errors=True)
        else:
            archived_output_path = study_outputs.outputs_path / f"{output_id}.zip"
            if archived_output_path.exists():
                archived_output_path.unlink()
            else:
                raise OutputNotFound(output_id)
        remove_from_cache(self._cache, study_id)

    @override
    def write_output_to_dir(self, study_id: str, output_id: str, parent: Path) -> None:
        """
        Writes outputs in filestudy format into parent directory
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        path_output = study_outputs.outputs_path / output_id
        path_output_zip = study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}"

        if path_output.is_dir():
            shutil.copytree(path_output, parent / output_id, dirs_exist_ok=False)
        elif path_output_zip.is_file():
            unarchive(path_output_zip, parent / output_id)
        else:
            raise OutputNotFound(output_id)

    @override
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
        Args:
            output_id: output id
            target: path of the file to export to

        Returns: zip file with study files compressed inside
        """
        study_outputs = self._outputs_provider.get_outputs(study_id)

        logger.info(f"Exporting output {output_id} from study {study_id}")

        path_output = study_outputs.outputs_path / output_id
        path_output_zip = study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}"

        if path_output_zip.exists():
            shutil.copyfile(path_output_zip, target)
            return None

        if not path_output.exists() and not path_output_zip.exists():
            raise OutputNotFound(output_id)

        stopwatch = StopWatch()
        if not path_output_zip.exists():
            archive_dir(path_output, target, archive_format=ArchiveFormat.ZIP)
        stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} from study {study_id} exported in {x}s"))

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

        archive_dir(
            study_outputs.outputs_path / output_id,
            study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}",
            remove_source_dir=True,
            archive_format=ArchiveFormat.ZIP,
        )
        remove_from_cache(self._cache, study_id)

    def _remote_unarchive(self, output_id: str, study_outputs: FileStudyOutputs) -> None:
        dest = study_outputs.outputs_path / output_id
        src = study_outputs.outputs_path / f"{output_id}{ArchiveFormat.ZIP}"
        self._remote_executor.execute_remote_task(
            f"unarchive_{study_outputs.study_workspace}",
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
        workspace = study_outputs.study_workspace
        if workspace != DEFAULT_WORKSPACE_NAME:
            self._remote_unarchive(output_id, study_outputs)
            remove_from_cache(self._cache, study_id)
        else:
            study_outputs = self._outputs_provider.get_outputs(study_id)
            outputs_path = study_outputs.outputs_path
            try:
                # TODO: should remove the zip ?
                unzip(outputs_path / output_id, outputs_path / f"{output_id}{ArchiveFormat.ZIP}")
                remove_from_cache(self._cache, study_id)
            except Exception as e:
                # TODO: we should probably raise here and remove partially unzipped files
                logger.warning(
                    f"Failed to unarchive study {study_id} output {output_id}",
                    exc_info=e,
                )

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
        mc_years: Optional[Sequence[int]] = None,
    ) -> Iterator[pd.DataFrame]:
        study_outputs = self._outputs_provider.get_outputs(study_id)
        aggregator_manager = AggregatorManager(
            study_outputs.outputs_path / output_id,
            query_file,
            frequency,
            ids_to_consider,
            columns_names,
            transform_columns_headers,
            mc_years,
        )
        return aggregator_manager.aggregate_output_data()

    @override
    def extract_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        study_outputs = self._outputs_provider.get_outputs(study_id)
        return extract_variables_list(study_outputs.outputs_path / output_id)

    @override
    def get_logs(self, study_id: str, output_id: str, job_id: str, err_log: bool) -> str:
        study_outputs = self._outputs_provider.get_outputs(study_id)
        file_study = study_outputs.get_file_study()
        log_locations = {
            False: [
                ["output", "logs", f"{job_id}-out.log"],
                ["output", "logs", f"{output_id}-out.log"],
                ["output", output_id, "antares-out"],
                ["output", output_id, "simulation"],
            ],
            True: [
                ["output", "logs", f"{job_id}-err.log"],
                ["output", "logs", f"{output_id}-err.log"],
                ["output", output_id, "antares-err"],
            ],
        }
        empty_log = False
        for log_location in log_locations[err_log]:
            try:
                # Assume UTF-8 but ignore errors, it's difficult to be sure of log encoding
                # especially because of windows error messages
                log = cast(
                    bytes,
                    file_study.tree.get(log_location, depth=1, formatted=True),
                ).decode(encoding="utf-8", errors="replace")
                # when missing file, RawFileNode return empty bytes
                if log:
                    return log
                else:
                    empty_log = True
            except ChildNotFoundError:
                pass
            except KeyError:
                pass
        if empty_log:
            return ""
        raise ChildNotFoundError(f"Logs for {output_id} of study {study_id} were not found")

    def _save_logs(
        self,
        study_id: str,
        job_id: str,
        log_suffix: str,
        log_data: str,
    ) -> None:
        logger.info(f"Saving logs for job {job_id} of study {study_id}")
        stopwatch = StopWatch()
        study_outputs = self._outputs_provider.get_outputs(study_id)
        file_study = study_outputs.get_file_study()
        file_study.tree.save(
            bytes(log_data, encoding="utf-8"),
            [
                "output",
                "logs",
                f"{job_id}-{log_suffix}",
            ],
        )
        stopwatch.log_elapsed(lambda d: logger.info(f"Saved logs for job {job_id} in {d}s"))
