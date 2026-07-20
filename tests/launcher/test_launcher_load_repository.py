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
from datetime import UTC, datetime

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import LauncherCache
from antarest.launcher.repository import LauncherCacheRepository
from tests.helpers import with_db_context

launcher_load_1 = LauncherCache(
    launcher_name="foo",
    allocated_cpu_rate=0.1,
    cluster_load_rate=0.2,
    nb_queued_jobs=3,
    launcher_status="TEST 1",
    date=datetime.now(UTC),
)

launcher_load_2 = LauncherCache(
    launcher_name="bar",
    allocated_cpu_rate=0.4,
    cluster_load_rate=0.5,
    nb_queued_jobs=10,
    launcher_status="TEST 2",
    date=datetime.now(UTC),
)

launcher_load_2_updated = LauncherCache(
    launcher_name="bar",
    allocated_cpu_rate=0.1,
    cluster_load_rate=1.0,
    nb_queued_jobs=100,
    launcher_status="TEST 2 BIS",
    date=datetime.now(UTC),
)


class TestLauncherCacheRepository(LauncherCacheRepository):
    def __init__(self) -> None:
        super().__init__()

    def get_launchers_loads(self) -> list[LauncherCache]:
        return db.session.query(LauncherCache).all()


@with_db_context
def test_database_launcher_loads_is_empty_by_default() -> None:
    db_launcher_load = TestLauncherCacheRepository()

    assert db_launcher_load.get_launchers_loads() == []


@with_db_context
def test_should_be_able_to_add_launcher_load_data_to_db() -> None:
    db_launcher_load = TestLauncherCacheRepository()
    db_launcher_load.update_launcher_load(launcher_load_1)

    actual_launchers_loads = db_launcher_load.get_launchers_loads()
    assert len(actual_launchers_loads) == 1

    check_launcher_load_equals(actual_launchers_loads[0], launcher_load_1)


@with_db_context
def test_should_be_able_to_update_launcher_load_data_from_db() -> None:
    db_launcher_load = TestLauncherCacheRepository()
    db_launcher_load.update_launcher_load(launcher_load_2)

    actual_launchers_loads = db_launcher_load.get_launchers_loads()
    assert len(actual_launchers_loads) == 1

    check_launcher_load_equals(actual_launchers_loads[0], launcher_load_2)

    db_launcher_load.update_launcher_load(launcher_load_2_updated)
    actual_launchers_loads = db_launcher_load.get_launchers_loads()
    assert len(actual_launchers_loads) == 1

    check_launcher_load_equals(actual_launchers_loads[0], launcher_load_2_updated)


@with_db_context
def test_should_be_able_to_update_multiple_launchers_loads_data_from_db() -> None:
    db_launcher_load = TestLauncherCacheRepository()
    db_launcher_load.update_launcher_load(launcher_load_1)
    db_launcher_load.update_launcher_load(launcher_load_2)

    assert len(db_launcher_load.get_launchers_loads()) == 2

    assert_launcher_load_is_in_db(launcher_load_1, db_launcher_load)
    assert_launcher_load_is_in_db(launcher_load_2, db_launcher_load)

    db_launcher_load.update_launcher_load(launcher_load_2_updated)
    assert len(db_launcher_load.get_launchers_loads()) == 2

    assert_launcher_load_is_in_db(launcher_load_2_updated, db_launcher_load)


@with_db_context
def test_should_update_all_launcher_loads_data_from_db() -> None:
    db_launcher_load = TestLauncherCacheRepository()
    db_launcher_load.update_all_launcher_loads({"foo": launcher_load_1.to_dto(), "bar": launcher_load_2.to_dto()})

    assert len(db_launcher_load.get_launchers_loads()) == 2
    assert_launcher_load_is_in_db(launcher_load_1, db_launcher_load)
    assert_launcher_load_is_in_db(launcher_load_2, db_launcher_load)

    db_launcher_load.update_all_launcher_loads(
        {"foo": launcher_load_1.to_dto(), "bar": launcher_load_2_updated.to_dto()}
    )

    assert len(db_launcher_load.get_launchers_loads()) == 2
    assert_launcher_load_is_in_db(launcher_load_1, db_launcher_load)
    assert_launcher_load_is_in_db(launcher_load_2_updated, db_launcher_load)


def assert_launcher_load_is_in_db(
    expected_launcher_load: LauncherCache, db_launcher_load: TestLauncherCacheRepository
) -> None:
    actual_launchers_loads = db_launcher_load.get_launchers_loads()

    actual_load = [
        load for load in actual_launchers_loads if load.launcher_name == expected_launcher_load.launcher_name
    ]
    assert len(actual_load) == 1
    check_launcher_load_equals(actual_load[0], expected_launcher_load)


def check_launcher_load_equals(actual_launcher_load: LauncherCache, expected_launcher_load: LauncherCache) -> None:
    assert actual_launcher_load.launcher_name == expected_launcher_load.launcher_name
    assert actual_launcher_load.allocated_cpu_rate == expected_launcher_load.allocated_cpu_rate
    assert actual_launcher_load.cluster_load_rate == expected_launcher_load.cluster_load_rate
    assert actual_launcher_load.nb_queued_jobs == expected_launcher_load.nb_queued_jobs
    assert actual_launcher_load.launcher_status == expected_launcher_load.launcher_status
