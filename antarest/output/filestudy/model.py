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
from dataclasses import dataclass
from enum import Enum, StrEnum
from functools import cached_property
from pathlib import Path
from typing import Callable, Generic, Iterable, Literal, Sequence, TypeAlias, TypeVar

import polars as pl

from antarest.core.exceptions import OutputSubFolderNotFound
from antarest.study.model import MatrixFrequency

"""Column name for the Monte Carlo year."""
MCYEAR_COL = "mcYear"

"""Column name for the time index."""
TIME_ID_COL = "timeId"


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


class MCIndAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksQueryFile(StrEnum):
    VALUES = "values"


class MCAllLinksQueryFile(StrEnum):
    VALUES = "values"
    ID = "id"


QueryFileType: TypeAlias = MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile

AggregationType: TypeAlias = Literal["mc-all", "mc-ind"]


@dataclass(frozen=True, slots=True)
class VariableDescription:
    """
    Represents the metadata of an output file column.

    Could probably be refined, see descriptions below, to better represent the actual usage (mc-all/mc-ind, details/values ...)

    Attributes:
        name: the name of the variable. Sometimes, used for an element name such as a cluster name (for example in
              "details" files).
        unit: unit of the variable. In output files ("details" files), this is actually sometimes used as a substitute
              for the name (NP COST - Euro for example), because the variable name is actually used for the cluster name.
        statistic_type: for mc-all outputs, this defines what statistic this represents: expectations, standard dev,
                        min, max ...
    """

    name: str
    unit: str | None
    statistic_type: str | None

    def to_tuple(self) -> tuple[str, str, str]:
        # Follows convention of output files ... maybe better keep it instead of None after all ?
        return self.name, self.unit_repr(), self.statistic_type_repr()

    def unit_repr(self) -> str:
        """
        Representation of the unit as in output files, never None.
        """
        return self.unit or " "

    def statistic_type_repr(self) -> str:
        """
        Representation of the statistic type as in output files, never None.
        """
        return self.statistic_type or ""

    def normal_repr(self) -> str:
        """
        That "normal form" is :
         - for mc-ind, only the variable name "Var"
         - for mc-all, the concatenation of variable name and stat type in upper case ... "VAR EXP"

        Cannot see any justification for that convention, it's inherited implicit choices from the past,
        could be changed in the future.
        """
        mc_ind = self.statistic_type is None
        if mc_ind:
            return self.name
        return f"{self.name} {self.statistic_type_repr()}".upper().strip()


def get_output_object_type(
    file_type: QueryFileType, is_link: bool
) -> Literal["areas", "links", "thermal_clusters", "renewable_clusters", "short_term_storages"]:
    if is_link:
        return "links"

    match file_type:
        case MCIndAreasQueryFile.DETAILS:
            return "thermal_clusters"
        case MCIndAreasQueryFile.DETAILS_RES:
            return "renewable_clusters"
        case MCIndAreasQueryFile.DETAILS_ST_STORAGE:
            return "short_term_storages"
        case _:
            return "areas"


C = TypeVar("C")
C2 = TypeVar("C2")


@dataclass(frozen=True)
class OutputDataFrame(Generic[C]):
    """
    We separate the polars dataframe and its headers as polars does not handle multi-headers columns.

    Attributes:
        C: Type holding columns metadata
    """

    data: pl.DataFrame
    headers: Sequence[C]

    def __post_init__(self) -> None:
        if len(self.headers) != len(self.data.columns):
            raise ValueError("The number of headers must match the number of columns in the dataframe")

    def map_metadata(self, func: Callable[[C], C2]) -> "OutputDataFrame[C2]":
        return OutputDataFrame(self.data, [func(col) for col in self.headers])


def find_mode_dir(output_dir: Path) -> Path:
    """
    Identifies economy or adequacy dir

    Raises:
        OutputSubFolderNotFound: when no folder matches.
    """
    for mode_name in ("economy", "adequacy"):
        mode_dir = output_dir / mode_name
        if mode_dir.exists():
            return mode_dir
    raise OutputSubFolderNotFound(output_dir.name, "economy|adequacy")


class FileOutput:
    """
    Provides a collection of methods to inspect the content of an output directory.

    Caches properties that may take some time to build (typically going through files), for efficiency.

    Attributes:
        output_dir (Path): The path to the output directory typically (<study_dir>/outputs/<output_id>).
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    @cached_property
    def mc_years(self) -> list[int]:
        mode_dir = find_mode_dir(self.output_dir)
        mc_ind_dir = mode_dir / "mc-ind"
        if not mc_ind_dir.exists():
            return []
        return sorted(int(d.name) for d in mc_ind_dir.iterdir())

    @property
    def first_mc_year(self) -> int:
        return self.mc_years[0]

    @property
    def mode(self) -> str:
        return self.mode_dir.name

    @cached_property
    def mode_dir(self) -> Path:
        return find_mode_dir(self.output_dir)

    @property
    def mc_all_dir(self) -> Path:
        return self.mode_dir / "mc-all"

    @property
    def mc_ind_dir(self) -> Path:
        return self.mode_dir / "mc-ind"

    def get_mc_year_dir(self, year: int) -> Path:
        return self.mc_ind_dir / f"{year:05d}"

    @cached_property
    def mc_ind_link_ids(self) -> tuple[str, ...]:
        """
        IDs of links that have data in mc-ind, sorted.
        """
        return tuple(sorted(d.name for d in self.iter_links_dir(self.first_mc_year)))

    @cached_property
    def mc_ind_area_ids(self) -> tuple[str, ...]:
        """
        IDs of areas that have data in mc-ind, sorted.
        """
        return tuple(sorted(d.name for d in self.iter_areas_dir(self.first_mc_year)))

    @cached_property
    def mc_all_link_ids(self) -> tuple[str, ...]:
        """
        IDs of links that have data in mc-all, sorted.
        """
        links_dir = self.mc_all_dir / "links"
        return tuple(sorted(d.name for d in links_dir.iterdir()))

    @cached_property
    def mc_all_area_ids(self) -> tuple[str, ...]:
        """
        IDs of areas that have data in mc-all, sorted.
        """
        areas_dir = self.mc_all_dir / "areas"
        return tuple(sorted(d.name for d in areas_dir.iterdir()))

    def iter_areas_dir(self, mc_year: int) -> Iterable[Path]:
        """
        No ordering guarantee.
        """
        return (self.get_mc_year_dir(mc_year) / "areas").iterdir()

    def iter_links_dir(self, mc_year: int) -> Iterable[Path]:
        """
        No ordering guarantee.
        """
        return (self.get_mc_year_dir(mc_year) / "links").iterdir()

    def get_mc_all_file(
        self,
        file_type: MCAllAreasQueryFile | MCAllLinksQueryFile,
        area_id: str,
        frequency: MatrixFrequency,
    ) -> Path | None:
        """
        Returns the path corresponding to the specified data, if it exists.
        """
        element_type = "areas" if isinstance(file_type, MCAllAreasQueryFile) else "links"
        file_path = self.mc_all_dir / element_type / area_id / f"{file_type}-{frequency}.txt"
        return file_path if file_path.exists() else None

    def get_mc_ind_file(
        self,
        mc_year: int,
        file_type: MCIndAreasQueryFile | MCIndLinksQueryFile,
        area_id: str,
        frequency: MatrixFrequency,
    ) -> Path | None:
        """
        Returns the path corresponding to the specified data, if it exists.
        """
        element_type = "areas" if isinstance(file_type, MCIndAreasQueryFile) else "links"
        file_path = self.get_mc_year_dir(mc_year) / element_type / area_id / f"{file_type}-{frequency}.txt"
        return file_path if file_path.exists() else None
