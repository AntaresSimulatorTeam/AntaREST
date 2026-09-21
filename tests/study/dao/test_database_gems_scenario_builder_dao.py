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

import importlib.util
import json
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.scenario_builder import GemsScenarioBuilder
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.scenario_builder import GEMS_SCENARIO_BUILDER_TABLE
from antarest.study.model import STUDY_VERSION_9_3
from tests.conftest import build_db_dao


def test_groups_are_stored_per_study(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    builder = GemsScenarioBuilder(scenario_groups={"load": {0: 1, 1: 5}, "hydro": {2: 7}})
    other_builder = GemsScenarioBuilder(scenario_groups={"load": {0: 3}})
    first.save_gems_scenario_builder(builder)
    second.save_gems_scenario_builder(other_builder)

    table = GEMS_SCENARIO_BUILDER_TABLE
    study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first.get_study_id())
    )
    rows = db_session.execute(select(table).where(table.c.study_data_id == study_data_id)).all()
    assert {row.scenario_group: json.loads(row.data) for row in rows} == {
        "load": {"0": 1, "1": 5},
        "hydro": {"2": 7},
    }
    assert first.get_gems_scenario_builder() == builder
    assert second.get_gems_scenario_builder() == other_builder

    replacement = GemsScenarioBuilder(scenario_groups={"load": {0: 9}, "wind": {1: 4}})
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
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    dao.save_gems_scenario_builder(GemsScenarioBuilder(scenario_groups={"load": {0: 1}, "hydro": {0: 2}}))
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
    replacement = GemsScenarioBuilder(scenario_groups={"load": {0: 4}})
    dao.save_gems_scenario_builder(replacement)
    assert dao.get_gems_scenario_builder() == replacement
    assert db_session.scalar(text("SELECT scenario_group FROM scenario_group_reference")) == "load"

    with pytest.raises(IntegrityError):
        dao.save_gems_scenario_builder(GemsScenarioBuilder(scenario_groups={"wind": {0: 5}}))
    # Neither the insertion nor the deletion is persisted when a reference prevents the replacement.
    assert dao.get_gems_scenario_builder() == replacement
    with pytest.raises(IntegrityError):
        dao.save_gems_scenario_builder(GemsScenarioBuilder())
    assert dao.get_gems_scenario_builder() == replacement


def test_migration_matches_table(db_engine: Engine) -> None:
    path = Path(__file__).resolve().parents[3] / "alembic/versions/95838f16cb00_create_gems_scenario_builder_table.py"
    spec = importlib.util.spec_from_file_location("gems_scenario_builder_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    table = GEMS_SCENARIO_BUILDER_TABLE
    with db_engine.begin() as connection:
        table.drop(connection)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            inspector = inspect(connection)
            columns = inspector.get_columns(table.name)
            assert [(c["name"], str(c["type"]), c["nullable"]) for c in columns] == [
                (c.name, str(c.type.compile(dialect=connection.dialect)), c.nullable) for c in table.columns
            ]
            assert inspector.get_pk_constraint(table.name)["constrained_columns"] == ["study_data_id", "scenario_group"]
            foreign_keys = inspector.get_foreign_keys(table.name)
            assert len(foreign_keys) == 1
            assert foreign_keys[0]["constrained_columns"] == ["study_data_id"]
            assert foreign_keys[0]["referred_table"] == "study_data"
            assert foreign_keys[0]["referred_columns"] == ["study_data_id"]
            assert foreign_keys[0]["options"]["ondelete"] == "CASCADE"
            migration.downgrade()
            assert not inspect(connection).has_table(table.name)
            migration.upgrade()
