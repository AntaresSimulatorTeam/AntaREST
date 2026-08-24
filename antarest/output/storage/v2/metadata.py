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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.output.filestudy.model import VariableDescription
from antarest.output.model import MatrixIndex
from antarest.output.storage.v2.dbmodel import (
    DbParquetArea,
    DbParquetOutput,
    DbParquetVariable,
    ElementType,
    ScenarioAggregation,
)
from antarest.output.storage.v2.variables_fetching import VariablesIndex
from antarest.study.model import MatrixFrequency


@dataclass(frozen=True)
class AreaVariables:
    """
    Attributes:
        area_id: Area identifier
        variables: Indices of variables for that area, in the parquet file (does not include the index offset for now ...).
    """

    area_id: str
    variables: Sequence[int]


class IParquetOutputMetadata(ABC):
    """
    Centralizes access to all kind of metadata for one parquet output:
    MC years, areas, variables ...
    """

    @property
    @abstractmethod
    def mc_years(self) -> list[int]:
        """
        The list of MC years for which the output contains some data
        """

    @abstractmethod
    def get_time_index(self, frequency: MatrixFrequency) -> MatrixIndex:
        """
        Time index for the specified frequency
        """

    @abstractmethod
    def get_variables(
        self, aggregation: ScenarioAggregation, element_type: ElementType
    ) -> Sequence[VariableDescription]:
        """
        The list of variables for the specified mc-ind/mc-year aggregation and element_type,
        in the same order as the corresponding columns in parquet files.
        """

    @property
    @abstractmethod
    def mc_ind_areas(self) -> Sequence[AreaVariables]:
        """
        The list of areas for mc-ind results, and the corresponding variables for which they have data.
        """


class ParquetOuputMetadataImpl(IParquetOutputMetadata):
    """
    Implementation which gets metadata from the DB, as lazily as possible.

    Caches retrieved data for re-use.
    """

    def __init__(self, session: Session, output_id: int) -> None:
        self.session = session
        self.output_id = output_id

    @cached_property
    def db_output(self) -> DbParquetOutput:
        return self.session.execute(select(DbParquetOutput).where(DbParquetOutput.id == self.output_id)).scalar_one()

    @cached_property
    def db_areas(self) -> Sequence[DbParquetArea]:
        return (
            self.session.execute(select(DbParquetArea).where(DbParquetArea.output_id == self.output_id))
            .scalars()
            .fetchall()
        )

    @cached_property
    def db_vars(self) -> Sequence[DbParquetVariable]:
        return (
            self.session.execute(select(DbParquetVariable).where(DbParquetVariable.output_id == self.output_id))
            .scalars()
            .fetchall()
        )

    @cached_property
    def variables_index(self) -> VariablesIndex:
        return VariablesIndex(self.db_vars)

    @override
    def get_variables(
        self, aggregation: ScenarioAggregation, element_type: ElementType
    ) -> Sequence[VariableDescription]:
        return self.variables_index.get_variables(aggregation, element_type)

    @override
    @property
    def mc_years(self) -> list[int]:
        return self.db_output.mc_years

    @override
    def get_time_index(self, frequency: MatrixFrequency) -> MatrixIndex:
        # TODO: get it from current implementation
        return MatrixIndex()

    @override
    @property
    def mc_ind_areas(self) -> Sequence[AreaVariables]:
        return tuple(AreaVariables(area_id=a.area_id, variables=a.mc_ind_vars) for a in self.db_areas)
