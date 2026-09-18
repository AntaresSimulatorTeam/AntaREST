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
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import InstrumentedAttribute, Session
from typing_extensions import override

from antarest.output.filestudy.model import VariableDescription
from antarest.output.model import MatrixIndex, OutputVariablesList
from antarest.output.storage.v2.dbmodel import (
    DbOutputMetadataV2,
    DbParquetArea,
    DbParquetBindingConstraint,
    DbParquetCluster,
    DbParquetLink,
    DbParquetVariable,
    ElementType,
    ScenarioAggregation,
)
from antarest.output.storage.v2.layout import CLUSTER_TYPES, OBJECT_NAMES
from antarest.study.model import MatrixFrequency
from antarest.study.storage.utils import SimulationRangeDefinition, get_matrix_index


@dataclass(frozen=True)
class ElementVariables:
    element_id: str
    year: int
    frequency: str
    variables: list[int]
    positions: list[int]
    cluster_id: str | None = None


class IParquetOutputMetadata(ABC):
    """Column descriptions and memberships are authoritative, never parquet column names."""

    @property
    @abstractmethod
    def mc_years(self) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def get_time_index(self, frequency: MatrixFrequency) -> MatrixIndex:
        raise NotImplementedError

    @abstractmethod
    def get_variables(
        self, aggregation: ScenarioAggregation, element_type: ElementType
    ) -> Sequence[VariableDescription]:
        raise NotImplementedError

    @abstractmethod
    def get_elements(
        self,
        aggregation: ScenarioAggregation,
        element_type: ElementType,
        frequency: MatrixFrequency | None = None,
        years: Sequence[int] = (),
        elements: Sequence[str] = (),
    ) -> Sequence[ElementVariables]:
        raise NotImplementedError


class ParquetOutputMetadata(IParquetOutputMetadata):
    def __init__(self, session: Session, output_id: int) -> None:
        self.session = session
        self.output_id = output_id
        self._variables: dict[tuple[ScenarioAggregation, ElementType], list[VariableDescription]] = {}

    @cached_property
    def db_output(self) -> DbOutputMetadataV2:
        return self.session.execute(
            select(DbOutputMetadataV2).where(DbOutputMetadataV2.id == self.output_id)
        ).scalar_one()

    @property
    @override
    def mc_years(self) -> list[int]:
        return self.db_output.mc_years

    @override
    def get_time_index(self, frequency: MatrixFrequency) -> MatrixIndex:
        m = self.db_output
        return get_matrix_index(
            SimulationRangeDefinition(
                starting_month=m.start_month,
                january_1st_weekday=m.january_first_weekday,
                leap_year=m.leap_year,
                start_day=m.start_day,
                end_day=m.end_day,
                first_weekday=m.first_weekday,
            ),
            is_output=True,
            level=frequency,
        )

    @override
    def get_variables(
        self, aggregation: ScenarioAggregation, element_type: ElementType
    ) -> Sequence[VariableDescription]:
        key = aggregation, element_type
        if key not in self._variables:
            rows = self.session.scalars(
                select(DbParquetVariable)
                .where(
                    DbParquetVariable.output_id == self.output_id,
                    DbParquetVariable.scenario_aggregation == aggregation,
                    DbParquetVariable.element_type == element_type,
                )
                .order_by(DbParquetVariable.column)
            )
            self._variables[key] = [VariableDescription(v.name, v.unit, v.statistic_type) for v in rows]
        return self._variables[key]

    @override
    def get_elements(
        self,
        aggregation: ScenarioAggregation,
        element_type: ElementType,
        frequency: MatrixFrequency | None = None,
        years: Sequence[int] = (),
        elements: Sequence[str] = (),
    ) -> Sequence[ElementVariables]:
        # Query only memberships belonging to the requested objects, years and frequency.
        table: type[DbParquetArea] | type[DbParquetLink] | type[DbParquetCluster] | type[DbParquetBindingConstraint]
        id_col: ColumnElement[str] | InstrumentedAttribute[str]
        if element_type in CLUSTER_TYPES:
            table = DbParquetCluster
            id_col = DbParquetCluster.area_id
        elif element_type in ("link", "link_id"):
            table = DbParquetLink
            id_col = DbParquetLink.area_1_id + " - " + DbParquetLink.area_2_id
        elif element_type == "binding_constraint":
            table = DbParquetBindingConstraint
            id_col = DbParquetBindingConstraint.constraint_id
        else:
            table = DbParquetArea
            id_col = DbParquetArea.area_id
        stmt = select(table, id_col.label("element_id")).where(
            table.output_id == self.output_id,
            table.scenario_aggregation == aggregation,
            table.element_type == element_type,
        )
        if frequency is not None:
            stmt = stmt.where(table.frequency == frequency.value)
        if years:
            stmt = stmt.where(table.mc_year.in_(years))
        if elements:
            stmt = stmt.where(id_col.in_(elements))
        stmt = stmt.order_by(table.mc_year, id_col)
        return [
            ElementVariables(
                element_id=element_id,
                year=row.mc_year,
                frequency=row.frequency,
                variables=row.columns,
                positions=row.positions,
                cluster_id=row.cluster_id if isinstance(row, DbParquetCluster) else None,
            )
            for row, element_id in self.session.execute(stmt)
        ]

    def get_variables_list(self) -> OutputVariablesList:
        result: dict[str, Any] = {}
        for aggregation in ("mc-ind", "mc-all"):
            areas: dict[str, dict[str, Any]] = {}
            links: dict[str, dict[str, Any]] = {}
            for element_type in ("area", "area_id", "link", "link_id", *CLUSTER_TYPES):
                variables = self.get_variables(aggregation, element_type)
                for element in self.get_elements(aggregation, element_type):
                    if element_type in ("link", "link_id"):
                        a1, a2 = element.element_id.split(" - ", 1)
                        item = links.setdefault(
                            element.element_id,
                            {
                                "area_1_name": a1,
                                "area_2_name": a2,
                                "variables": set(),
                            },
                        )
                    else:
                        item = areas.setdefault(element.element_id, {"name": element.element_id, "variables": set()})
                    if element.cluster_id is None:
                        item["variables"].update(variables[i].normal_repr() for i in element.variables)
                    else:
                        clusters = item.setdefault(OBJECT_NAMES[element_type], {})
                        cluster = clusters.setdefault(
                            element.cluster_id, {"name": element.cluster_id, "variables": set()}
                        )
                        cluster["variables"].update(variables[i].unit_repr() for i in element.variables)
            for area in areas.values():
                for kind in CLUSTER_TYPES:
                    key = OBJECT_NAMES[kind]
                    if key in area:
                        area[key] = list(area[key].values())
            result[aggregation.replace("-", "_")] = {
                "areas": [areas[k] for k in sorted(areas)],
                "links": [links[k] for k in sorted(links)],
            }
        return OutputVariablesList.model_validate(result)
