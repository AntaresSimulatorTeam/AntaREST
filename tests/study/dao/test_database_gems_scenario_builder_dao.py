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

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.scenario_builder import GEMS_SCENARIO_BUILDER_TABLE
from tests.study.dao.conftest import build_db_dao_10_2


def test_groups_are_stored_per_study(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    first = build_db_dao_10_2(db_session, matrix_service)
    second = build_db_dao_10_2(db_session, matrix_service)
    builder = GemsScenarioBuilder(
        scenarios={
            "load": [
                GemsScBuilderMapping(scenario=0, time_series_index=1),
                GemsScBuilderMapping(scenario=1, time_series_index=5),
            ],
            "hydro": [GemsScBuilderMapping(scenario=2, time_series_index=7)],
        }
    )
    other_builder = GemsScenarioBuilder(scenarios={"load": [GemsScBuilderMapping(scenario=0, time_series_index=3)]})
    first.save_gems_scenario_builder(builder)
    second.save_gems_scenario_builder(other_builder)

    table = GEMS_SCENARIO_BUILDER_TABLE
    study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first.get_study_id())
    )
    rows = db_session.execute(select(table).where(table.c.study_data_id == study_data_id)).all()
    assert {row.scenario_group: json.loads(row.data) for row in rows} == {
        "load": [{"scenario": 0, "time_series_index": 1}, {"scenario": 1, "time_series_index": 5}],
        "hydro": [{"scenario": 2, "time_series_index": 7}],
    }
    assert first.get_gems_scenario_builder() == builder
    assert second.get_gems_scenario_builder() == other_builder

    replacement = GemsScenarioBuilder(
        scenarios={
            "load": [GemsScBuilderMapping(scenario=0, time_series_index=9)],
            "wind": [GemsScBuilderMapping(scenario=1, time_series_index=4)],
        }
    )
    first.save_gems_scenario_builder(replacement)
    assert first.get_gems_scenario_builder() == replacement
    assert second.get_gems_scenario_builder() == other_builder
    first.save_gems_scenario_builder(GemsScenarioBuilder())
    assert first.get_gems_scenario_builder() is None
    assert second.get_gems_scenario_builder() == other_builder
    first.save_gems_scenario_builder(builder)

    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == study_data_id))
    db_session.commit()
    assert first.get_gems_scenario_builder() is None
    assert second.get_gems_scenario_builder() == other_builder


def test_save_preserves_referenced_groups(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)
    dao.save_gems_scenario_builder(
        GemsScenarioBuilder(
            scenarios={
                "load": [GemsScBuilderMapping(scenario=0, time_series_index=1)],
                "hydro": [GemsScBuilderMapping(scenario=0, time_series_index=2)],
            }
        )
    )
    study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == dao.get_study_id())
    )
    # Exercise the future use of a composite foreign key targeting a scenario group.
    db_session.execute(
        text(
            "CREATE TABLE scenario_group_reference (study_data_id INTEGER, scenario_group VARCHAR(255), "
            "FOREIGN KEY (study_data_id, scenario_group) "
            "REFERENCES gems_scenario_builder (study_data_id, scenario_group))"
        )
    )
    db_session.execute(
        text("INSERT INTO scenario_group_reference VALUES (:study_data_id, 'load')"),
        {"study_data_id": study_data_id},
    )
    db_session.commit()
    replacement = GemsScenarioBuilder(scenarios={"load": [GemsScBuilderMapping(scenario=0, time_series_index=4)]})
    dao.save_gems_scenario_builder(replacement)
    assert dao.get_gems_scenario_builder() == replacement
    assert db_session.scalar(text("SELECT scenario_group FROM scenario_group_reference")) == "load"

    with pytest.raises(IntegrityError):
        dao.save_gems_scenario_builder(
            GemsScenarioBuilder(scenarios={"wind": [GemsScBuilderMapping(scenario=0, time_series_index=5)]})
        )
    # Neither the insertion nor the deletion is persisted when a reference prevents the replacement.
    assert dao.get_gems_scenario_builder() == replacement
    with pytest.raises(IntegrityError):
        dao.save_gems_scenario_builder(GemsScenarioBuilder())
    assert dao.get_gems_scenario_builder() == replacement
