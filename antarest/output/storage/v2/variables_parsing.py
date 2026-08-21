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

"""
Extraction of variables metadata from file studies, in order to populate the database
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from antarest.output.filestudy.matrixfiles import get_start_column, parse_headers
from antarest.output.filestudy.model import FileOutput, MCAllAreasQueryFile, MCIndAreasQueryFile, VariableDescription
from antarest.output.storage.v2.dbmodel import DbParquetArea, DbParquetVariable, ElementType, ScenarioAggregation
from antarest.study.model import MatrixFrequency

# TODO: Possibly a better naming to find than "parsing results"


@dataclass(frozen=True)
class ParsingResultPart:
    """
    A list of variables, and for each area the list of variables, as a list of indices.

    Results from the parsing of a set of files for one element type, and either mc-ind or mc-all
    """

    variables: list[VariableDescription]
    area_vars: dict[str, list[int]]


@dataclass(frozen=True)
class OutputParsingResult:
    """
    Intermediate data structure from which we'll populate the database.
    """

    mc_ind_areas: ParsingResultPart
    mc_all_areas: ParsingResultPart


def parse_area_variables(file_output: FileOutput, aggregation: ScenarioAggregation) -> ParsingResultPart:
    var_cols: dict[VariableDescription, int] = {}
    vars: list[VariableDescription] = []
    area_cols: dict[str, list[int]] = {}

    get_file: Callable[[str, MatrixFrequency], Path | None]
    match aggregation:
        case "mc-ind":

            def get_file(element_id: str, freq: MatrixFrequency) -> Path | None:
                return file_output.get_mc_ind_file(
                    file_output.first_mc_year, MCIndAreasQueryFile.VALUES, element_id, freq
                )
        case "mc-all":

            def get_file(element_id: str, freq: MatrixFrequency) -> Path | None:
                return file_output.get_mc_all_file(MCAllAreasQueryFile.VALUES, element_id, freq)

    for element_id in file_output.area_ids:
        # searching for the first existing "frequency"
        for freq in MatrixFrequency:
            if data_file := get_file(element_id, freq):
                with open(data_file) as f:
                    area_vars = parse_headers(f, get_start_column(freq))

                for v in area_vars:
                    if v not in var_cols:
                        var_cols[v] = len(vars)
                        vars.append(v)

                area_cols[element_id] = [var_cols[v] for v in area_vars]
                break  # other frequencies will have the same variables

    return ParsingResultPart(variables=vars, area_vars=area_cols)


def parse_output_variables(file_output: FileOutput) -> OutputParsingResult:
    """
    Extract area "values" variables from the output
    """

    return OutputParsingResult(
        mc_all_areas=parse_area_variables(file_output, "mc-all"),
        mc_ind_areas=parse_area_variables(file_output, "mc-ind"),
    )


def _convert_to_db_vars(
    output_id: int, aggregation: ScenarioAggregation, elt_type: ElementType, vars: list[VariableDescription]
) -> list[DbParquetVariable]:
    return [
        DbParquetVariable(
            output_id=output_id,
            scenario_aggregation=aggregation,
            element_type=elt_type,
            column=c,
            name=v.name,
            unit=v.unit,
            statistic_type=v.statistic_type,
        )
        for c, v in enumerate(vars)
    ]


def extract_output_variables_to_database(session: Session, output_id: int, file_output: FileOutput) -> None:
    """
    Parses variables from file output an dump them to database.
    """
    parsing_result = parse_output_variables(file_output)

    variables: list[DbParquetVariable] = []
    areas: list[DbParquetArea] = []

    mc_all_areas = parsing_result.mc_all_areas
    mc_ind_areas = parsing_result.mc_ind_areas
    variables.extend(_convert_to_db_vars(output_id, "mc-all", "area", mc_all_areas.variables))
    variables.extend(_convert_to_db_vars(output_id, "mc-ind", "area", mc_ind_areas.variables))

    mc_ind_area_vars = mc_ind_areas.area_vars
    mc_all_area_vars = mc_all_areas.area_vars
    area_ids = sorted(set(mc_all_area_vars).union(mc_ind_area_vars))
    for area_id in area_ids:
        areas.append(
            DbParquetArea(
                output_id=output_id,
                area_id=area_id,
                mc_all_vars=mc_all_area_vars.get(area_id, []),
                mc_ind_vars=mc_ind_area_vars.get(area_id, []),
            )
        )

    session.add_all(variables)
    session.add_all(areas)
