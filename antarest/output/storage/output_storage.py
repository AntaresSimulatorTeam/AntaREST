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
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd
import polars as pl

from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.output.filestudy.utils import (
    QueryFileType,
)
from antarest.output.model.output_data import (
    MatrixAggregationResultDTO,
    MatrixIndex,
    StudyDownloadDTO,
)
from antarest.output.model.output_metadata import OutputDetails, OutputMetadata, OutputStorageType
from antarest.output.model.variables_metadata import OutputVariablesList
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)


class IOutputStorage(ABC):
    """
    Provides access to stored outputs.

    That API must not be dependent on a particular storage implementation, in particular
    on the antares-solver file format.
    """

    @property
    @abstractmethod
    def storage_type(self) -> OutputStorageType:
        raise NotImplementedError()

    @abstractmethod
    def import_outputs(self, study_id: str, src_outputs_dir: Path) -> None:
        """
        Import outputs when importing a study that contains outputs.
        """

    @abstractmethod
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name_suffix: str | None = None,
        logs: SimulationLogs = SimulationLogs.no_logs(),
    ) -> str:
        """
        Import an outputs to the storage.

        Currently accepts either:
         - a binary IO, in which case either a zip or 7z file is expected, with no nested directories.
         - a path to a zip file, with no nested directories.
         - a path to a directory, where the actual output dir could be a child of that directory.

        In the case of a zip file path, the output will be considered archived.

        This behaviour is inherited from legacy implementation, it should be clarified.

        Args:
            study_id: the study id
            output: either a path to a directory or a zip, or binary IO corresponding to the content of an archive.
            output_name_suffix: Optional name suffix to append to the output name, for example "hello" will
                                appear at the end of the output name as "20201014-1422eco-hello"

        Returns: the output identifier inside the study
        """

    @abstractmethod
    def list_outputs(self, study_id: str) -> list[OutputMetadata]:
        """
        Get the list of outputs for a study.
        """

    @abstractmethod
    def get_output_details(self, study_id: str) -> list[OutputDetails]:
        """
        Get the list of output for a study.
        """

    @abstractmethod
    def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:
        """
        Copies one output to another study. Note that the copied output will be created in this storage.
        """

    @abstractmethod
    def delete_output(self, study_id: str, output_id: str) -> None:
        """
        Delete a simulation output
        """

    @abstractmethod
    def write_output_to_dir(self, study_id: str, output_id: str, parent: Path) -> None:
        """
        Writes outputs in filestudy format into the specified parent directory.
        """

    @abstractmethod
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip.
        """

    @abstractmethod
    def output_exists(self, study_id: str, output_id: str) -> bool:
        """Check if a study output exists."""

    @abstractmethod
    def is_output_archived(self, study_id: str, output_id: str) -> bool:
        """Check if a study output is archived."""

    @abstractmethod
    def archive_study_output(self, study_id: str, output_id: str) -> None:
        """Archive a study output."""

    # noinspection SpellCheckingInspection
    @abstractmethod
    def unarchive_study_output(self, study_id: str, output_id: str) -> None:
        """Un-archive a study output."""

    @abstractmethod
    def get_digest(self, study_id: str, output_id: str) -> DigestUI:
        """
        Digest of the output.
        """

    @abstractmethod
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

    @abstractmethod
    def iterate_output_data(
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
        """
        Iterates over output data based on several filtering conditions, as a stream of dataframes.
        """

    # TODO: find better naming ?
    @abstractmethod
    def get_matrix_aggregation_result(
        self, study_id: str, output_id: str, request: StudyDownloadDTO
    ) -> MatrixAggregationResultDTO:
        """
        Deprecated feature: returns some output data as a possibly large in-memory model.
        Just another view of the underlying output data, still used by some clients.
        """

    @abstractmethod
    def get_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        """
        Get variables list of this output.
        """

    @abstractmethod
    def get_logs(self, study_id: str, output_id: str, log_type: LogType) -> str:
        """
        Retrieve logs.
        """

    @abstractmethod
    def get_disk_usage(self, study_id: str, output_id: str) -> int:
        """
        Retrieve disk usage for a specific output.
        """

    @abstractmethod
    def get_raw_content(self, study_id: str, output_id: str, url: list[str], formatted: bool) -> Any:
        """
        Retrieves raw content based on a given url
        """

    @abstractmethod
    def get_matrix_as_dataframe(
        self, study_id: str, output_id: str, url: list[str], frequency: MatrixFrequency
    ) -> pd.DataFrame:
        """
        Parses a matrix from a given url and returns it as a dataframe
        """

    @abstractmethod
    def get_original_file(self, study_id: str, output_id: str, url: list[str]) -> OriginalFile:
        """
        Retrieves the original file as it exists on the file system
        """
