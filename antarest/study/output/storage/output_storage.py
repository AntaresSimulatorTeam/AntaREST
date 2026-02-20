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
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Iterator, Optional, Sequence

import pandas as pd
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.model import MatrixFrequency, MatrixIndex
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.utils import QueryFileType
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestUI

logger = logging.getLogger(__name__)


class OutputStorageType(StrEnum):
    IN_STUDY_FILE_TREE = "IN_STUDY_FILE_TREE"
    V2 = "V2"


@dataclass(frozen=True)
class OutputMetadata:
    """
    Simplest metadata for a study output.

    Attributes:
        id:       unique identifier of the output
        in_study: whether the output is stored in the study file tree. Here the abstraction is clearly leaky,
                  but we need it for compatibility with existing file studies.
    """

    id: str
    in_study: bool
    archived: bool


class OutputDetails(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )

    name: str
    mode: Mode
    synthesis: bool
    by_year: bool
    nb_years: int
    archived: bool


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
        output_name_suffix: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import an outputs to the storage.

        Accepts either a binary input, in which case either a zip or 7z file is expected,
        or a path, in which case only uncompressed or zip is handled (?).
        Note that in the case of a zip file path, the output will be considered archived.

        Args:
            study_id: the study id
            output: Path of the output or raw data
            output_name: Optional name suffix to append to the output name

        Returns: None
        """

    @abstractmethod
    def list_outputs(self, study_id: str) -> list[OutputMetadata]:
        """
        Get the list of outputs for a study.
        """

    @abstractmethod
    def get_output_details(self, study_id: str, output_id: str) -> OutputDetails:
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
