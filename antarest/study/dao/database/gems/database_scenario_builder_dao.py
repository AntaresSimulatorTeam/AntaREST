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

import json

from sqlalchemy import CursorResult, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import GemsScenarioAlreadyExists, GemsScenarioNotFound
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.study.business.model.gems.scenario_builder import (
    GemsScBuilderMapping,
    GemsScenarioBuilder,
    ScenarioBuilderMapping,
)
from antarest.study.dao.api.gems_scenario_builder_dao import GemsScenarioBuilderDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.scenario_builder import GEMS_SCENARIO_BUILDER_TABLE


class DatabaseGemsScenarioBuilderDao(GemsScenarioBuilderDao, DatabaseDaoBase):
    @override
    def get_gems_scenario_builder(self) -> GemsScenarioBuilder | None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        rows = self._db_session.execute(select(table).where(table.c.study_data_id == self._study_data_id)).fetchall()
        if not rows:
            return None
        return GemsScenarioBuilder(scenarios={row.scenario_group: json.loads(row.data) for row in rows})

    @override
    def save_gems_scenario_builder(self, scenario_builder: GemsScenarioBuilder) -> None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        session = self._db_session
        groups = scenario_builder.model_dump(mode="json")["scenarios"]
        # todo: we should fill the default value before saving in DB
        try:
            upsert_multiple(
                session,
                table,
                [
                    {"study_data_id": self._study_data_id, "scenario_group": group, "data": json.dumps(data)}
                    for group, data in groups.items()
                ],
            )
            session.execute(
                delete(table).where(
                    (table.c.study_data_id == self._study_data_id) & table.c.scenario_group.not_in(groups)
                )
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise

    @override
    def add_scenario_to_gems_scenario_builder(
        self, scenario_name: str, mapping: ScenarioBuilderMapping
    ) -> ScenarioBuilderMapping:
        filled_scenario = self._fill_missing_years(mapping)
        table = GEMS_SCENARIO_BUILDER_TABLE
        session = self._db_session
        values = [
            {"study_data_id": self._study_data_id, "scenario_group": scenario_name, "data": json.dumps(filled_scenario)}
        ]

        stmt = insert(table).values(values)
        try:
            session.execute(stmt)
            session.commit()
        except IntegrityError as e:
            # Means the scenario already existed
            session.rollback()
            raise GemsScenarioAlreadyExists(scenario_name, self._study_id) from e

        return filled_scenario

    @override
    def remove_scenario_from_gems_scenario_builder(self, scenario_name: str) -> None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        session = self._db_session
        result = session.execute(
            delete(table).where(
                (table.c.study_data_id == self._study_data_id) & (table.c.scenario_group == scenario_name)
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount == 0:
            # Means the DELETE had no effect, so the scenario group did not exist
            raise GemsScenarioNotFound(scenario_name, self._study_id)

        session.commit()

    def _fill_missing_years(self, mapping: ScenarioBuilderMapping) -> list[GemsScBuilderMapping]:
        """
        GEMS scenario builder has default values for missing years, we should initialize them for the front-end
        """
        result = []
        simulation_nb_years = self.get_impl().get_general_config().nb_years
        for year in range(simulation_nb_years):
            obj_mapping = {"scenario": year, "time_series_index": mapping.get(year, year + 1)}
            result.append(GemsScBuilderMapping.model_validate(obj_mapping))
        return result
