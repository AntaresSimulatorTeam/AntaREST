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
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Iterator, List, Optional, Sequence

import pandas as pd

from antarest.study.model import MatrixFrequency, MatrixIndex, StudySimResultDTO
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.utils import QueryFileType
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)


class OutputStorageType(StrEnum):
    FILE_TREE = "FILE_TREE"
    PARQUET = "PARQUET"


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
    def import_output(
        self,
        study_id: str,
        output: BinaryIO | Path,
        output_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import an outputs to the storage.

        Args:
            study_id: the study id
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name
        Returns: None
        """

    @abstractmethod
    def get_study_sim_result(self, study_id: str) -> List[StudySimResultDTO]:
        """
        Get the list of output for a study
        """

    @abstractmethod
    def delete_output(self, study_id: str, output_id: str) -> None:
        """
        Delete a simulation output
        """

    @abstractmethod
    def export_output(self, study_id: str, output_id: str, target: Path) -> None:
        """
        Export and compresses study inside zip
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
        """
        Aggregates output data based on several filtering conditions, as a stream of dataframes.
        """

    @abstractmethod
    def extract_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        """
        Extract variables list from output.
        """
