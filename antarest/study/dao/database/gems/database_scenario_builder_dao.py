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
from typing import Any

from sqlalchemy import CursorResult, Row, delete, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import GemsScenarioNotFound
from antarest.core.model import GemsId
from antarest.core.utils.sql_utils import upsert_multiple
from antarest.study.business.model.gems.scenario_builder import (
    GemsScBuilderMapping,
    GemsScBuilderMappings,
    GemsScenarioBuilder,
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
    def save_scenario_inside_gems_scenario_builder(self, scenario_name: GemsId, data: GemsScBuilderMappings) -> None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        session = self._db_session
        values = [
            {
                "study_data_id": self._study_data_id,
                "scenario_group": scenario_name,
                "data": json.dumps([mapping.model_dump() for mapping in data]),
            }
        ]

        try:
            upsert_multiple(session, table, values)
            session.commit()
        except Exception as e:
            # Probably means the study did not exist in the first place or a weird error occurred in DB.
            session.rollback()
            raise e

    @override
    def remove_scenario_from_gems_scenario_builder(self, scenario_name: GemsId) -> None:
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

    @override
    def scenario_exists_in_gems_scenario_builder(self, scenario_name: GemsId) -> bool:
        return self._fetch_scenario(scenario_name) is not None

    def _fetch_scenario(self, scenario_name: GemsId) -> Row[Any] | None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        return self._db_session.execute(
            select(table).where(
                (table.c.study_data_id == self._study_data_id) & (table.c.scenario_group == scenario_name)
            )
        ).fetchone()

    @override
    def get_scenario_from_gems_scenario_builder(self, scenario_name: GemsId) -> GemsScBuilderMappings:
        row = self._fetch_scenario(scenario_name)

        if not row:
            raise GemsScenarioNotFound(scenario_name, self._study_id)

        return [GemsScBuilderMapping.model_validate(mapping) for mapping in json.loads(row.data)]
