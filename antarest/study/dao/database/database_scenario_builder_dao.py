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
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table
from typing_extensions import override

from antarest.study.business.model.scenario_builder_model import AnyScenarios, Ruleset, ScenarioType
from antarest.study.dao.api.scenario_builder_dao import ScenarioBuilderDao
from antarest.study.dao.database.models.ruleset import (
    SCENARIO_BINDING_CONSTRAINTS_TABLE,
    SCENARIO_HYDRO_FINAL_LEVEL_TABLE,
    SCENARIO_HYDRO_GENERATION_POWER_TABLE,
    SCENARIO_HYDRO_INITIAL_LEVEL_TABLE,
    SCENARIO_HYDRO_TABLE,
    SCENARIO_LOAD_TABLE,
    SCENARIO_NTC_TABLE,
    SCENARIO_RENEWABLE_TABLE,
    SCENARIO_SOLAR_TABLE,
    SCENARIO_STORAGE_CONSTRAINTS_TABLE,
    SCENARIO_STORAGE_INFLOWS_TABLE,
    SCENARIO_THERMAL_TABLE,
    SCENARIO_WIND_TABLE,
)

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao

_LINK_SEPARATOR = " / "

_AREA_FIELD_TO_TABLE: dict[str, Table] = {
    "load": SCENARIO_LOAD_TABLE,
    "hydro": SCENARIO_HYDRO_TABLE,
    "wind": SCENARIO_WIND_TABLE,
    "solar": SCENARIO_SOLAR_TABLE,
    "hydro_initial_levels": SCENARIO_HYDRO_INITIAL_LEVEL_TABLE,
    "hydro_final_levels": SCENARIO_HYDRO_FINAL_LEVEL_TABLE,
    "hydro_generation_power": SCENARIO_HYDRO_GENERATION_POWER_TABLE,
}

_AREA_SCENARIO_TYPE_TO_TABLE: dict[ScenarioType, Table] = {
    ScenarioType.LOAD: SCENARIO_LOAD_TABLE,
    ScenarioType.HYDRO: SCENARIO_HYDRO_TABLE,
    ScenarioType.WIND: SCENARIO_WIND_TABLE,
    ScenarioType.SOLAR: SCENARIO_SOLAR_TABLE,
    ScenarioType.HYDRO_INITIAL_LEVEL: SCENARIO_HYDRO_INITIAL_LEVEL_TABLE,
    ScenarioType.HYDRO_FINAL_LEVEL: SCENARIO_HYDRO_FINAL_LEVEL_TABLE,
    ScenarioType.HYDRO_GENERATION_POWER: SCENARIO_HYDRO_GENERATION_POWER_TABLE,
}

_AREA_ITEM_TABLE_MAP: dict[ScenarioType, tuple[Table, str]] = {
    ScenarioType.THERMAL: (SCENARIO_THERMAL_TABLE, "thermal_id"),
    ScenarioType.RENEWABLE: (SCENARIO_RENEWABLE_TABLE, "renewable_id"),
    ScenarioType.SHORT_TERM_STORAGE_INFLOWS: (SCENARIO_STORAGE_INFLOWS_TABLE, "st_storage_id"),
}


class DatabaseScenarioBuilderDao(ScenarioBuilderDao):
    """
    Database implementation of ScenarioBuilderDao.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def save_scenario_builder(self, ruleset: Ruleset) -> None:
        study_id, session = self._study_id, self._db_session

        # Delete all existing scenario data for the study
        all_tables = [
            *_AREA_FIELD_TO_TABLE.values(),
            SCENARIO_NTC_TABLE,
            SCENARIO_BINDING_CONSTRAINTS_TABLE,
            *(t for t, _ in _AREA_ITEM_TABLE_MAP.values()),
            SCENARIO_STORAGE_CONSTRAINTS_TABLE,
        ]
        for table in all_tables:
            session.execute(delete(table).where(table.c.study_id == study_id))

        base = {"study_id": study_id}

        for field_name, table in _AREA_FIELD_TO_TABLE.items():
            scenarios: dict[str, Any] = getattr(ruleset, field_name)
            if scenarios:
                session.execute(
                    insert(table),
                    [{**base, "area_id": area_id, "value": ts} for area_id, ts in scenarios.items()],
                )

        if ruleset.ntc:
            session.execute(
                insert(SCENARIO_NTC_TABLE),
                [
                    {
                        **base,
                        "area1": link_id.split(_LINK_SEPARATOR)[0],
                        "area2": link_id.split(_LINK_SEPARATOR)[1],
                        "value": ts,
                    }
                    for link_id, ts in ruleset.ntc.items()
                ],
            )

        if ruleset.binding_constraints:
            session.execute(
                insert(SCENARIO_BINDING_CONSTRAINTS_TABLE),
                [{**base, "bc_group_id": bc_id, "value": ts} for bc_id, ts in ruleset.binding_constraints.items()],
            )

        for scenario_type, (table, id_col) in _AREA_ITEM_TABLE_MAP.items():
            scenarios = ruleset.get(scenario_type)
            if scenarios:
                rows = [
                    {**base, "area_id": area_id, id_col: item_id, "value": ts}
                    for area_id, items in scenarios.items()
                    for item_id, ts in items.items()
                ]
                if rows:
                    session.execute(insert(table), rows)

        if ruleset.storage_constraints:
            rows = [
                {
                    **base,
                    "area_id": area_id,
                    "st_storage_id": storage_id,
                    "constraint_id": constraint_id,
                    "value": ts,
                }
                for area_id, storages in ruleset.storage_constraints.items()
                for storage_id, constraints in storages.items()
                for constraint_id, ts in constraints.items()
            ]
            if rows:
                session.execute(insert(SCENARIO_STORAGE_CONSTRAINTS_TABLE), rows)

        session.commit()

    @override
    def get_ruleset(self) -> Ruleset:
        study_id, session = self._study_id, self._db_session
        ruleset = Ruleset()

        for field_name, table in _AREA_FIELD_TO_TABLE.items():
            stmt = select(table).where(table.c.study_id == study_id)
            scenarios = {row.area_id: row.value for row in session.execute(stmt)}
            if scenarios:
                setattr(ruleset, field_name, scenarios)

        stmt = select(SCENARIO_NTC_TABLE).where(SCENARIO_NTC_TABLE.c.study_id == study_id)
        ntc = {f"{row.area1}{_LINK_SEPARATOR}{row.area2}": row.value for row in session.execute(stmt)}
        if ntc:
            ruleset.ntc = ntc

        stmt = select(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
            SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == study_id
        )
        bc = {row.bc_group_id: row.value for row in session.execute(stmt)}
        if bc:
            ruleset.binding_constraints = bc

        for scenario_type, (table, id_col) in _AREA_ITEM_TABLE_MAP.items():
            stmt = select(table).where(table.c.study_id == study_id)
            result: dict[str, dict[str, Any]] = {}
            for row in session.execute(stmt):
                result.setdefault(row.area_id, {})[getattr(row, id_col)] = row.value
            if result:
                ruleset.set(scenario_type, result)

        stmt = select(SCENARIO_STORAGE_CONSTRAINTS_TABLE).where(
            SCENARIO_STORAGE_CONSTRAINTS_TABLE.c.study_id == study_id
        )
        storage_constraints: dict[str, dict[str, dict[str, Any]]] = {}
        for row in session.execute(stmt):
            storage_constraints.setdefault(row.area_id, {}).setdefault(row.st_storage_id, {})[row.constraint_id] = (
                row.value
            )
        if storage_constraints:
            ruleset.storage_constraints = storage_constraints

        return ruleset

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        study_id, session = self._study_id, self._db_session

        if scenario_type in _AREA_SCENARIO_TYPE_TO_TABLE:
            table = _AREA_SCENARIO_TYPE_TO_TABLE[scenario_type]
            stmt = select(table).where(table.c.study_id == study_id)
            return {row.area_id: row.value for row in session.execute(stmt)}

        if scenario_type == ScenarioType.LINK:
            stmt = select(SCENARIO_NTC_TABLE).where(SCENARIO_NTC_TABLE.c.study_id == study_id)
            return {f"{row.area1}{_LINK_SEPARATOR}{row.area2}": row.value for row in session.execute(stmt)}

        if scenario_type == ScenarioType.BINDING_CONSTRAINTS:
            stmt = select(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == study_id
            )
            return {row.bc_group_id: row.value for row in session.execute(stmt)}

        if scenario_type in _AREA_ITEM_TABLE_MAP:
            table, id_col = _AREA_ITEM_TABLE_MAP[scenario_type]
            stmt = select(table).where(table.c.study_id == study_id)
            result: dict[str, Any] = {area_id: {} for area_id in self.get_impl().get_all_area_ids()}
            for row in session.execute(stmt):
                result.setdefault(row.area_id, {})[getattr(row, id_col)] = row.value
            return result

        if scenario_type == ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
            stmt = select(SCENARIO_STORAGE_CONSTRAINTS_TABLE).where(
                SCENARIO_STORAGE_CONSTRAINTS_TABLE.c.study_id == study_id
            )
            constraints_result: dict[str, Any] = {
                area_id: {storage_id: {} for storage_id in storages}
                for area_id, storages in self.get_impl().get_all_st_storages().items()
            }
            for area_id in self.get_impl().get_all_area_ids():
                constraints_result.setdefault(area_id, {})
            for row in session.execute(stmt):
                constraints_result.setdefault(row.area_id, {}).setdefault(row.st_storage_id, {})[row.constraint_id] = (
                    row.value
                )
            return constraints_result

        raise ValueError(f"Unknown scenario type {scenario_type}")
