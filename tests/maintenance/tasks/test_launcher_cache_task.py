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

from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from antarest.core.config import Config, LauncherConfig, LocalConfig, SlurmConfig, StorageConfig
from antarest.core.utils.utils import current_time
from antarest.launcher.adapters.abstract_load import AbstractLoad
from antarest.launcher.adapters.local_launcher.local_load import LocalLoad
from antarest.launcher.adapters.slurm_launcher.slurm_load import SlurmLoad
from antarest.launcher.load_service import LoadService
from antarest.launcher.model import LauncherLoad, LauncherLoadDTO
from antarest.launcher.repository import LauncherLoadRepository
from antarest.launcher.ssh_client import SlurmError
from antarest.maintenance.tasks.common import BackGroundTaskStatus, MaintenanceContextNotFoundError
from antarest.maintenance.tasks.launcher_cache_task import save_launcher_cache_task
from tests.helpers import with_db_context
from tests.maintenance.conftest import celery_app


def _build_load_service(tmp_path: Path, loads: dict[str, AbstractLoad]) -> LoadService:
    config = Config(
        storage=StorageConfig(tmp_dir=tmp_path),
        launcher=LauncherConfig(default="local", configs=[LocalConfig(id="local", name="name")]),
    )
    return LoadService(
        config=config,
        loads=loads,
        launcher_load_repository=LauncherLoadRepository(),
    )


class _FakeContext:
    """Minimal stand-in for `MaintenanceContext`, exposing only the `load_service` attribute
    the task under test reads."""

    def __init__(self, load_service: LoadService) -> None:
        self.load_service = load_service


@pytest.fixture
def with_maintenance_ctx():
    """Install a fake `MaintenanceContext` (exposing only `load_service`) for the duration of the
    test, and restore the previous value afterward. Mirrors `with_no_maintenance_ctx` from
    `tests/maintenance/conftest.py`, but installs a usable context instead of `None`."""

    def _install(load_service: LoadService) -> None:
        celery_app.conf.maintenance_ctx = _FakeContext(load_service)

    original_ctx = getattr(celery_app.conf, "maintenance_ctx", None)
    yield _install
    celery_app.conf.maintenance_ctx = original_ctx


class TestSaveLauncherCacheTask:
    @patch(
        "antarest.launcher.adapters.slurm_launcher.slurm_load.SlurmLoad.get_load",
        new=Mock(
            return_value=LauncherLoadDTO(
                allocated_cpu_rate=10, cluster_load_rate=0, nb_queued_jobs=2, launcher_status="SUCCESS"
            )
        ),
    )
    @with_db_context
    def test_load_read_back_from_db_is_naive_and_still_comparable(self, tmp_path: Path, with_maintenance_ctx) -> None:
        slurm_load = SlurmLoad(SlurmConfig(id="local", name="name"))
        load_service = _build_load_service(tmp_path, {"local": slurm_load})
        with_maintenance_ctx(load_service)

        result = save_launcher_cache_task.run.__wrapped__(save_launcher_cache_task)
        assert result.status == BackGroundTaskStatus.SUCCESS

        stored_load = load_service.launcher_cache_repository.get_launcher_load("local")
        assert stored_load is not None
        assert stored_load.date.tzinfo is None

        # Must not raise TypeError("can't compare offset-naive and offset-aware datetimes").
        assert load_service._is_outdated_load_data(stored_load) is False

    @with_db_context
    def test_stale_naive_date_is_correctly_reported_as_outdated(self, tmp_path: Path) -> None:
        load_service = _build_load_service(tmp_path, {"local": LocalLoad()})

        stale_naive_load = LauncherLoad(
            launcher_name="local",
            allocated_cpu_rate=0,
            cluster_load_rate=0,
            nb_queued_jobs=0,
            launcher_status="SUCCESS",
            date=current_time() - timedelta(days=1),
        )
        load_service.launcher_cache_repository.update_all_launcher_loads([stale_naive_load])

        stored_load = load_service.launcher_cache_repository.get_launcher_load("local")
        assert stored_load is not None
        assert stored_load.date.tzinfo is None
        assert load_service._is_outdated_load_data(stored_load) is True

    @with_db_context
    def test_returns_partial_success_when_one_launcher_fails(self, tmp_path: Path, with_maintenance_ctx) -> None:
        ok_load = LocalLoad()
        failing_load = Mock()
        failing_load.get_load.side_effect = SlurmError("unreachable")

        load_service = _build_load_service(tmp_path, {"local": ok_load, "slurm": failing_load})
        with_maintenance_ctx(load_service)

        result = save_launcher_cache_task.run.__wrapped__(save_launcher_cache_task)

        assert result.status == BackGroundTaskStatus.PARTIAL_SUCCESS
        # local launchers are not cached
        assert load_service.launcher_cache_repository.get_launcher_load("local") is None
        # slurm launcher failed to be cached
        assert load_service.launcher_cache_repository.get_launcher_load("slurm") is None

    @with_db_context
    def test_returns_success_when_all_launchers_succeed(self, tmp_path: Path, with_maintenance_ctx) -> None:
        load_service = _build_load_service(tmp_path, {"local": LocalLoad()})
        with_maintenance_ctx(load_service)

        result = save_launcher_cache_task.run.__wrapped__(save_launcher_cache_task)

        assert result.status == BackGroundTaskStatus.SUCCESS


def test_raises_without_context(with_no_maintenance_ctx: None) -> None:
    with pytest.raises(MaintenanceContextNotFoundError):
        save_launcher_cache_task.run()
