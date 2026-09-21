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

from sqlalchemy import insert, select
from typing_extensions import override

from antarest.core.exceptions import GemsScenarioBuilderAlreadyExists
from antarest.study.business.model.gems.scenario_builder import GemsScenarioBuilder
from antarest.study.dao.api.gems_scenario_builder_dao import GemsScenarioBuilderDao
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.gems.scenario_builder import GEMS_SCENARIO_BUILDER_TABLE


class DatabaseGemsScenarioBuilderDao(GemsScenarioBuilderDao, DatabaseDaoBase):
    @override
    def get_gems_scenario_builder(self) -> GemsScenarioBuilder | None:
        table = GEMS_SCENARIO_BUILDER_TABLE
        row = self._db_session.execute(select(table).where(table.c.study_data_id == self._study_data_id)).fetchone()
        if row is None:
            return None
        return GemsScenarioBuilder(scenario_groups=row.scenario_groups)

    @override
    def save_gems_scenario_builder(self, scenario_builder: GemsScenarioBuilder) -> None:
        if self.get_gems_scenario_builder() is not None:
            raise GemsScenarioBuilderAlreadyExists(f"A GEMS scenario builder already exists for study {self._study_id}")
        self._db_session.execute(
            insert(GEMS_SCENARIO_BUILDER_TABLE),
            {"study_data_id": self._study_data_id, **scenario_builder.model_dump(mode="json")},
        )
        self._db_session.commit()
