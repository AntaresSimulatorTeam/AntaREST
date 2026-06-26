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
from unittest.mock import MagicMock

from antarest.launcher.adapters.database_launcher_load_dao import DataBaseLauncherLoadDao
from antarest.launcher.model import LauncherLoad
from tests.helpers import with_db_context

launcher_load_1 = LauncherLoad(
    launcher_name="foo",
    allocated_cpu_rate=0.1,
    cluster_load_rate=0.2,
    nb_queued_jobs=3,
    launcher_status="TEST 1",
)

launcher_load_2 = LauncherLoad(
    launcher_name="bar",
    allocated_cpu_rate=0.4,
    cluster_load_rate=0.5,
    nb_queued_jobs=10,
    launcher_status="TEST 2",
)

launcher_load_2_updated = LauncherLoad(
    launcher_name="bar",
    allocated_cpu_rate=0.1,
    cluster_load_rate=1.0,
    nb_queued_jobs=100,
    launcher_status="TEST 2 BIS",
)


@with_db_context
def test_database_launcher_loads_is_empty_by_default() -> None:
    db_launcher_load = DataBaseLauncherLoadDao()

    assert db_launcher_load.get_launchers_loads() == []


@with_db_context
def test_should_be_able_to_add_launcher_load_data_to_db() -> None:
    db_launcher_load = DataBaseLauncherLoadDao()
    db_launcher_load.update_launcher_load(launcher_load_1)

    actual_launchers_loads = db_launcher_load.get_launchers_loads()
    assert len(actual_launchers_loads) == 1

    check_launcher_load_equals(actual_launchers_loads[0], launcher_load_1)


@with_db_context
def test_should_be_able_to_update_launcher_load_data_from_db() -> None:
    db_launcher_load = DataBaseLauncherLoadDao()
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
    db_launcher_load = DataBaseLauncherLoadDao()
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
    db_launcher_load = DataBaseLauncherLoadDao()
    service_mock = MagicMock()
    service_mock.get_all_loads.return_value = {"foo": launcher_load_1, "bar": launcher_load_2}
    db_launcher_load.update_all_launcher_loads(service_mock)

    assert len(db_launcher_load.get_launchers_loads()) == 2
    assert_launcher_load_is_in_db(launcher_load_1, db_launcher_load)
    assert_launcher_load_is_in_db(launcher_load_2, db_launcher_load)

    service_mock.get_all_loads.return_value = {"foo": launcher_load_1, "bar": launcher_load_2_updated}
    db_launcher_load.update_all_launcher_loads(service_mock)

    assert len(db_launcher_load.get_launchers_loads()) == 2
    assert_launcher_load_is_in_db(launcher_load_1, db_launcher_load)
    assert_launcher_load_is_in_db(launcher_load_2_updated, db_launcher_load)


def assert_launcher_load_is_in_db(
    expected_launcher_load: LauncherLoad, db_launcher_load: DataBaseLauncherLoadDao
) -> None:
    actual_launchers_loads = db_launcher_load.get_launchers_loads()

    actual_load = [
        load for load in actual_launchers_loads if load.launcher_name == expected_launcher_load.launcher_name
    ]
    assert len(actual_load) == 1
    check_launcher_load_equals(actual_load[0], expected_launcher_load)


def check_launcher_load_equals(actual_launcher_load: LauncherLoad, expected_launcher_load: LauncherLoad) -> None:
    assert actual_launcher_load.launcher_name == expected_launcher_load.launcher_name
    assert actual_launcher_load.allocated_cpu_rate == expected_launcher_load.allocated_cpu_rate
    assert actual_launcher_load.cluster_load_rate == expected_launcher_load.cluster_load_rate
    assert actual_launcher_load.nb_queued_jobs == expected_launcher_load.nb_queued_jobs
    assert actual_launcher_load.launcher_status == expected_launcher_load.launcher_status
