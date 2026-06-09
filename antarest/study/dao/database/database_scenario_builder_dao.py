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

from antarest.study.business.model.scenario_builder_model import (
    AnyScenarios,
    Ruleset,
    RulesetUpdate,
    ScenarioType,
    initialize_ruleset_with_version,
    update_ruleset,
)
from antarest.study.business.model.study_index import StudyIndex
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
        impl = self.get_impl()
        version = impl.get_version()
        nb_years = impl.get_general_config().nb_years
        years = [str(y) for y in range(nb_years)]
        index = self._build_study_index(scenario_type)

        dense = initialize_ruleset_with_version(years, index, version, {scenario_type})
        sparse = self.get_ruleset()
        update_ruleset(dense, RulesetUpdate(**sparse.model_dump()), version)
        return dense.get(scenario_type)

    def _build_study_index(self, scenario_type: ScenarioType) -> StudyIndex:
        """
        Build the study index for the given scenario type and the scenario only.
        This way we avoid performing a full study index build which is really costly.
        """
        impl = self.get_impl()

        areas = []
        links = []
        thermals = {}
        storages = {}
        bc_groups = []
        renewables = {}
        sts_additional_constraints = {}

        if scenario_type in {
            ScenarioType.LOAD,
            ScenarioType.THERMAL,
            ScenarioType.HYDRO,
            ScenarioType.WIND,
            ScenarioType.SOLAR,
            ScenarioType.RENEWABLE,
            ScenarioType.HYDRO_INITIAL_LEVEL,
            ScenarioType.HYDRO_FINAL_LEVEL,
            ScenarioType.HYDRO_GENERATION_POWER,
            ScenarioType.SHORT_TERM_STORAGE_INFLOWS,
            ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS,
        }:
            # For all of these scenarios, we need to get the list of areas
            areas = impl.get_all_area_ids()

            if scenario_type == ScenarioType.THERMAL:
                th_clusters = impl.get_all_thermals()
                thermals = {a: list(th_clusters.get(a, {})) for a in areas}

            if scenario_type == ScenarioType.RENEWABLE:
                renew_clusters = impl.get_all_renewables()
                renewables = {a: list(renew_clusters.get(a, {})) for a in areas}

            if scenario_type == ScenarioType.SHORT_TERM_STORAGE_INFLOWS:
                storages = {a: list(impl.get_all_st_storages().get(a, {})) for a in areas}

            if scenario_type == ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS:
                sts = impl.get_all_st_storages()
                sts_constraints = impl.get_all_st_storage_additional_constraints()
                sts_additional_constraints = {
                    a: {s: [c.id for c in sts_constraints.get(a, {}).get(s, [])] for s in sts.get(a, {})} for a in areas
                }

        if scenario_type == ScenarioType.LINK:
            links = [(link.area1, link.area2) for link in impl.get_links()]

        if scenario_type == ScenarioType.BINDING_CONSTRAINTS:
            bc_groups = list({c.group for c in impl.get_all_constraints().values() if c.group})

        return StudyIndex(
            areas=areas,
            links=links,
            thermals=thermals,
            renewables=renewables,
            storages=storages,
            bc_groups=bc_groups,
            sts_additional_constraints=sts_additional_constraints,
        )
