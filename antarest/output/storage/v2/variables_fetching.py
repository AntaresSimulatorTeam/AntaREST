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
Fetching variables metadata from the database
"""

from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.output.filestudy.model import VariableDescription
from antarest.output.storage.v2.dbmodel import DbParquetArea, DbParquetVariable, ElementType, ScenarioAggregation


class VariablesIndex:
    """
    Helper class to retrieve variable info from DB models.
    """

    def __init__(self, variables: Iterable[DbParquetVariable]) -> None:
        vars: dict[tuple[ScenarioAggregation, ElementType], list[DbParquetVariable]] = {}
        for v in variables:
            vars.setdefault((v.scenario_aggregation, v.element_type), []).append(v)

        self._variables = {k: sorted(v, key=lambda v: v.column) for k, v in vars.items()}  # sort by columns

    def _get_db_vars(self, aggregation: ScenarioAggregation, element_type: ElementType) -> Sequence[DbParquetVariable]:
        """
        Get all variables for the specified "mc-ind/mc-all" and element type (areas, links, ...)
        """
        return self._variables.get((aggregation, element_type), [])

    def get_variables(self, aggregation: ScenarioAggregation, element_type: ElementType) -> list[VariableDescription]:
        """
        Get all variables for the specified "mc-ind/mc-all" and element type (areas, links, ...)
        """
        return [_to_var_desc(v) for v in self._get_db_vars(aggregation, element_type)]


def _to_var_desc(db_var: DbParquetVariable) -> VariableDescription:
    return VariableDescription(db_var.name, db_var.unit, db_var.statistic_type)


def get_variables_index(session: Session, output_id: int) -> VariablesIndex:
    output_variables = session.execute(
        select(DbParquetVariable).where(DbParquetVariable.output_id == output_id)
    ).scalars()
    return VariablesIndex(output_variables)


def get_area_variables(
    session: Session, output_id: int, aggregation: ScenarioAggregation, area_id: str
) -> list[VariableDescription]:

    # All variables, should load fast ?
    variables_index = get_variables_index(session, output_id)

    # Get area information
    area = session.execute(select(DbParquetArea).where(DbParquetArea.area_id == area_id)).scalar_one()

    all_areas_vars = variables_index.get_variables(aggregation, "area")
    cols = area.mc_all_vars if aggregation == "mc-all" else area.mc_ind_vars
    return [all_areas_vars[c] for c in cols]
