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
"""Read only headers, and persist the variable catalogue and object memberships."""

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from antarest.output.filestudy.matrixfiles import get_start_column, parse_headers
from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.dbmodel import (
    DbParquetArea,
    DbParquetBindingConstraint,
    DbParquetCluster,
    DbParquetLink,
    DbParquetVariable,
    ElementColumns,
    ElementType,
    ScenarioAggregation,
)
from antarest.output.storage.v2.layout import SourceFile, header_groups, source_files


@dataclass
class ParsingResultPart:
    variables: list[VariableDescription] = field(default_factory=list)
    area_vars: dict[str, list[int]] = field(default_factory=dict)


@dataclass(frozen=True)
class Membership:
    source: SourceFile
    cluster_id: str | None
    columns: list[int]
    positions: list[int]


@dataclass
class OutputParsingResult:
    parts: dict[tuple[ScenarioAggregation, ElementType], ParsingResultPart] = field(default_factory=dict)
    memberships: list[Membership] = field(default_factory=list)

    @property
    def mc_ind_areas(self) -> ParsingResultPart:
        return self.parts.get(("mc-ind", "area"), ParsingResultPart())

    @property
    def mc_all_areas(self) -> ParsingResultPart:
        return self.parts.get(("mc-all", "area"), ParsingResultPart())


def parse_output_variables(file_output: FileOutput) -> OutputParsingResult:
    result = OutputParsingResult()
    indices: dict[tuple[ScenarioAggregation, ElementType], dict[VariableDescription, int]] = {}
    for source in source_files(file_output):
        key = source.aggregation, source.element_type
        part = result.parts.setdefault(key, ParsingResultPart())
        index = indices.setdefault(key, {})
        with source.path.open(encoding="utf-8") as content:
            headers = parse_headers(content, get_start_column(source.frequency))
        for group in header_groups(headers, source.element_type):
            columns = []
            for variable in group.variables:
                if variable not in index:
                    index[variable] = len(part.variables)
                    part.variables.append(variable)
                columns.append(index[variable])
            if source.element_type == "area":
                part.area_vars.setdefault(source.element_id, columns)
            result.memberships.append(Membership(source, group.cluster_id, columns, group.positions))
    return result


def extract_output_variables_to_database(session: Session, output_id: int, file_output: FileOutput) -> None:
    result = parse_output_variables(file_output)
    for (aggregation, element_type), part in result.parts.items():
        session.add_all(
            [
                DbParquetVariable(
                    output_id=output_id,
                    scenario_aggregation=aggregation,
                    element_type=element_type,
                    column=i,
                    name=v.name,
                    unit=v.unit,
                    statistic_type=v.statistic_type,
                )
                for i, v in enumerate(part.variables)
            ]
        )
    for membership in result.memberships:
        source = membership.source
        row: ElementColumns
        if source.element_type in ("link", "link_id"):
            area1, area2 = source.element_id.split(" - ", 1)
            row = DbParquetLink(area_1_id=area1, area_2_id=area2)
        elif membership.cluster_id is not None:
            row = DbParquetCluster(area_id=source.element_id, cluster_id=membership.cluster_id)
        elif source.element_type == "binding_constraint":
            row = DbParquetBindingConstraint(constraint_id=source.element_id)
        else:
            row = DbParquetArea(area_id=source.element_id)
        row.output_id = output_id
        row.scenario_aggregation = source.aggregation
        row.element_type = source.element_type
        row.frequency = source.frequency.value
        row.mc_year = source.year
        row.columns = membership.columns
        row.positions = membership.positions
        session.add(row)
    # The variables-list API also lists objects whose output directory is empty.
    roots: list[tuple[ScenarioAggregation, int, Path]] = [("mc-all", 0, file_output.mc_all_dir)]
    roots.extend(("mc-ind", year, file_output.get_mc_year_dir(year)) for year in file_output.mc_years)
    presence: DbParquetArea | DbParquetLink
    for aggregation, year, path in roots:
        for kind in ("areas", "links"):
            for folder in sorted((path / kind).glob("*")):
                if not folder.is_dir():
                    continue
                if kind == "areas":
                    presence = DbParquetArea(area_id=folder.name, element_type="area")
                else:
                    a1, a2 = folder.name.split(" - ", 1)
                    presence = DbParquetLink(area_1_id=a1, area_2_id=a2, element_type="link")
                presence.output_id = output_id
                presence.scenario_aggregation = aggregation
                presence.mc_year = year
                presence.frequency = ""
                presence.columns = []
                presence.positions = []
                session.add(presence)
    session.flush()
