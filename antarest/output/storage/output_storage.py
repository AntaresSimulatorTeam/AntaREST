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
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Iterator, Optional, Sequence, Any

import polars as pl
from pydantic import ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.output.filestudy.utils import QueryFileType
from antarest.output.model import OutputVariablesList
from antarest.study.business.model.config.general_model import Mode
from antarest.study.model import MatrixFrequency, MatrixIndex
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
                  but we need it for compatibility with existing file studies, at archival time, to decide if
                  the study should be archived separately or not.
    """

    id: str
    in_study: bool
    archived: bool


# The following settings class are used by a known client,
# we keep it here for compatibility reasons, but that could be removed in the future
class OutputSettingsGeneral(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    mode: str
    horizon: str
    nbyears: int
    simulation_start: int = Field(alias="simulation.start")
    simulation_end: int = Field(alias="simulation.end")
    january_1st: str = Field(alias="january.1st")
    first_month_in_year: str = Field(alias="first-month-in-year")
    first_weekday: str = Field(alias="first.weekday")
    leapyear: bool
    year_by_year: bool = Field(alias="year-by-year")
    user_playlist: bool = Field(alias="user-playlist")


class OutputSettingsOptimization(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )
    transmission_capacities: str | bool = Field(alias="transmission-capacities")


class OutputSettings(AntaresBaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    general: OutputSettingsGeneral
    optimization: OutputSettingsOptimization
    playlist: list[int] | None = None


class OutputDetails(AntaresBaseModel):
    """
    More detailed metadata about a study output.
    """

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
    storage_type: OutputStorageType

    settings: OutputSettings | None = Field(deprecated=True, default=None)

    @model_serializer(mode="wrap")
    def _serialize(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data: dict[str, object] = handler(self)
        if data.get("settings") is None:
            data.pop("settings", None)
        return data


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
    ) -> Iterator[pl.DataFrame]:
        """
        Aggregates output data based on several filtering conditions, as a stream of dataframes.
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
