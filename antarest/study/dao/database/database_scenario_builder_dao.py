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
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import RulesetNotFound
from antarest.study.business.model.scenario_builder_model import AnyScenarios, Ruleset, Rulesets, ScenarioType
from antarest.study.dao.api.scenario_builder_dao import ScenarioBuilderDao
from antarest.study.dao.database.models.ruleset import (
    ACTIVE_RULESET_TABLE,
    RULESET_AREA_ITEM_CONSTRAINT_TABLE,
    RULESET_AREA_ITEM_TABLE,
    RULESET_AREA_TABLE,
    RULESET_BC_GROUP_TABLE,
    RULESET_LINK_TABLE,
    RULESET_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

_AREA_SCENARIO_TYPES = {
    ScenarioType.LOAD,
    ScenarioType.HYDRO,
    ScenarioType.WIND,
    ScenarioType.SOLAR,
    ScenarioType.HYDRO_INITIAL_LEVEL,
    ScenarioType.HYDRO_FINAL_LEVEL,
    ScenarioType.HYDRO_GENERATION_POWER,
}

_AREA_ITEM_SCENARIO_TYPES = {
    ScenarioType.THERMAL,
    ScenarioType.RENEWABLE,
    ScenarioType.SHORT_TERM_STORAGE_INFLOWS,
}

_Row = dict[str, Any]


def _flatten_1_level(base_row: _Row, id_column: str, scenarios: dict[str, Any]) -> list[_Row]:
    return [{**base_row, id_column: entity_id, "timeseries": ts} for entity_id, ts in scenarios.items()]


def _flatten_2_levels(base_row: _Row, id_columns: tuple[str, str], scenarios: dict[str, Any]) -> list[_Row]:
    col1, col2 = id_columns
    return [
        row
        for entity_id, items in scenarios.items()
        for row in _flatten_1_level({**base_row, col1: entity_id}, col2, items)
    ]


def _flatten_3_levels(base_row: _Row, id_columns: tuple[str, str, str], scenarios: dict[str, Any]) -> list[_Row]:
    col1, col2, col3 = id_columns
    return [
        row
        for entity_id, items in scenarios.items()
        for row in _flatten_2_levels({**base_row, col1: entity_id}, (col2, col3), items)
    ]


class DatabaseScenarioBuilderDao(ScenarioBuilderDao):
    """
    Database implementation of ScenarioBuilderDao.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseScenarioBuilderDAO with dependencies.

        Args:
            study_id: The study ID for database queries.
            db_session: SQLAlchemy session for database operations.
        """
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @override
    def save_scenario_builder(self, rulesets: Rulesets) -> None:
        study_id, session = self._study_id, self._db_session

        # Delete all existing rulesets for the study
        session.execute(delete(RULESET_TABLE).where(RULESET_TABLE.c.study_id == study_id))

        ruleset_rows: list[_Row] = []
        area_rows: list[_Row] = []
        link_rows: list[_Row] = []
        bc_group_rows: list[_Row] = []
        area_item_rows: list[_Row] = []
        area_item_constraint_rows: list[_Row] = []

        for ruleset_name, ruleset in rulesets.items():
            ruleset_rows.append({"study_id": study_id, "ruleset_name": ruleset_name})
            base_row: _Row = {"study_id": study_id, "ruleset_name": ruleset_name}

            for scenario_type in ScenarioType:
                scenarios = ruleset.get(scenario_type)
                if not scenarios:
                    continue

                if scenario_type in _AREA_SCENARIO_TYPES:
                    area_rows += _flatten_1_level({**base_row, "scenario_type": scenario_type}, "area_id", scenarios)
                elif scenario_type == ScenarioType.LINK:
                    link_rows += _flatten_1_level(base_row, "link_id", scenarios)
                elif scenario_type == ScenarioType.BINDING_CONSTRAINTS:
                    bc_group_rows += _flatten_1_level(base_row, "bc_group_id", scenarios)
                elif scenario_type in _AREA_ITEM_SCENARIO_TYPES:
                    area_item_rows += _flatten_2_levels(
                        {**base_row, "scenario_type": scenario_type}, ("area_id", "item_id"), scenarios
                    )
                elif scenario_type == ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
                    area_item_constraint_rows += _flatten_3_levels(
                        base_row, ("area_id", "item_id", "constraint_id"), scenarios
                    )

        for table, rows in [
            (RULESET_TABLE, ruleset_rows),
            (RULESET_AREA_TABLE, area_rows),
            (RULESET_LINK_TABLE, link_rows),
            (RULESET_BC_GROUP_TABLE, bc_group_rows),
            (RULESET_AREA_ITEM_TABLE, area_item_rows),
            (RULESET_AREA_ITEM_CONSTRAINT_TABLE, area_item_constraint_rows),
        ]:
            if rows:
                session.execute(insert(table), rows)

        session.commit()

    @override
    def get_rulesets(self) -> Rulesets:
        study_id, session = self._study_id, self._db_session

        # Get all ruleset names
        stmt = select(RULESET_TABLE).where(RULESET_TABLE.c.study_id == study_id)
        rulesets: Rulesets = {row.ruleset_name: Ruleset() for row in session.execute(stmt)}

        # Area scenarios
        stmt = select(RULESET_AREA_TABLE).where(RULESET_AREA_TABLE.c.study_id == study_id)
        for row in session.execute(stmt):
            scenarios = rulesets[row.ruleset_name].get(row.scenario_type)
            scenarios[row.area_id] = row.timeseries

        # Link scenarios
        stmt = select(RULESET_LINK_TABLE).where(RULESET_LINK_TABLE.c.study_id == study_id)
        for row in session.execute(stmt):
            rulesets[row.ruleset_name].ntc[row.link_id] = row.timeseries

        # Binding constraints scenarios
        stmt = select(RULESET_BC_GROUP_TABLE).where(RULESET_BC_GROUP_TABLE.c.study_id == study_id)
        for row in session.execute(stmt):
            rulesets[row.ruleset_name].binding_constraints[row.bc_group_id] = row.timeseries

        # Area item scenarios
        stmt = select(RULESET_AREA_ITEM_TABLE).where(RULESET_AREA_ITEM_TABLE.c.study_id == study_id)
        for row in session.execute(stmt):
            scenarios = rulesets[row.ruleset_name].get(row.scenario_type)
            scenarios.setdefault(row.area_id, {})[row.item_id] = row.timeseries

        # Area item constraint scenarios
        stmt = select(RULESET_AREA_ITEM_CONSTRAINT_TABLE).where(
            RULESET_AREA_ITEM_CONSTRAINT_TABLE.c.study_id == study_id
        )
        for row in session.execute(stmt):
            rulesets[row.ruleset_name].storage_constraints.setdefault(row.area_id, {}).setdefault(row.item_id, {})[
                row.constraint_id
            ] = row.timeseries

        return rulesets

    @override
    def get_active_ruleset_name(self, default_ruleset: str = "Default Ruleset") -> str:
        study_id, session = self._study_id, self._db_session

        stmt = select(ACTIVE_RULESET_TABLE.c.ruleset_name).where(ACTIVE_RULESET_TABLE.c.study_id == study_id)
        result: str | None = session.execute(stmt).scalar_one_or_none()

        if result is None:
            return default_ruleset
        return result

    @override
    def save_active_ruleset_name(self, ruleset_name: str) -> None:
        session = self._db_session

        value = dict(study_id=self._study_id, ruleset_name=ruleset_name)

        try:
            upsert_one(session, ACTIVE_RULESET_TABLE, value)
        except IntegrityError as e:
            session.rollback()
            raise RulesetNotFound(ruleset_name) from e

        session.commit()

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        study_id, session = self._study_id, self._db_session
        ruleset_name = self.get_active_ruleset_name()

        if scenario_type in _AREA_SCENARIO_TYPES:
            table = RULESET_AREA_TABLE
            stmt = select(table).where(
                (table.c.study_id == study_id)
                & (table.c.ruleset_name == ruleset_name)
                & (table.c.scenario_type == scenario_type)
            )
            return {row.area_id: row.timeseries for row in session.execute(stmt)}

        if scenario_type == ScenarioType.LINK:
            table = RULESET_LINK_TABLE
            stmt = select(table).where((table.c.study_id == study_id) & (table.c.ruleset_name == ruleset_name))
            return {row.link_id: row.timeseries for row in session.execute(stmt)}

        if scenario_type == ScenarioType.BINDING_CONSTRAINTS:
            table = RULESET_BC_GROUP_TABLE
            stmt = select(table).where((table.c.study_id == study_id) & (table.c.ruleset_name == ruleset_name))
            return {row.bc_group_id: row.timeseries for row in session.execute(stmt)}

        if scenario_type in _AREA_ITEM_SCENARIO_TYPES:
            table = RULESET_AREA_ITEM_TABLE
            stmt = select(table).where(
                (table.c.study_id == study_id)
                & (table.c.ruleset_name == ruleset_name)
                & (table.c.scenario_type == scenario_type)
            )
            result: dict[str, Any] = {}
            for row in session.execute(stmt):
                result.setdefault(row.area_id, {})[row.item_id] = row.timeseries
            return result

        if scenario_type == ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
            table = RULESET_AREA_ITEM_CONSTRAINT_TABLE
            stmt = select(table).where((table.c.study_id == study_id) & (table.c.ruleset_name == ruleset_name))
            constraints_result: dict[str, Any] = {}
            for row in session.execute(stmt):
                constraints_result.setdefault(row.area_id, {}).setdefault(row.item_id, {})[row.constraint_id] = (
                    row.timeseries
                )
            return constraints_result

        raise ValueError(f"Unknown scenario type {scenario_type}")
