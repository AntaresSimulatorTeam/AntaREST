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


from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config, LauncherConfig, LocalConfig, StorageConfig
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.model import LauncherParametersDTO
from antarest.launcher.repository import LauncherCacheRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.ssh_client import SlurmError
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.launcher_cache_task import save_launcher_cache_task
from tests.helpers import with_db_context


def _build_launcher_service_with_real_local_launcher(tmp_path: Path) -> tuple[LauncherService, LocalLauncher]:
    """Builds a LauncherService backed by a real (not mocked) LocalLauncher and DB repository,
    so that the in-memory `submitted_jobs` state and the DB round-trip behave exactly as in
    production."""
    config = Config(
        storage=StorageConfig(tmp_dir=tmp_path),
        launcher=LauncherConfig(default="local", configs=[LocalConfig(id="local", name="name")]),
    )

    factory_launcher_mock = Mock()
    local_launcher = LocalLauncher(
        config.launcher.configs[0],
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),  # type: ignore[union-attr]
    )
    factory_launcher_mock.build_launcher.return_value = {"local": local_launcher}

    service = LauncherService(
        config=config,
        study_service=Mock(),
        output_service=Mock(),
        login_service=Mock(),
        job_result_repository=Mock(),
        solver_presets_repository=Mock(),
        launcher_cache_repository=LauncherCacheRepository(),
        event_bus=Mock(),
        factory_launcher=factory_launcher_mock,
        file_transfer_manager=Mock(),
        task_service=Mock(),
        cache=Mock(),
    )
    return service, local_launcher


class TestSaveLauncherCacheTask:
    @with_db_context
    def test_load_read_back_from_db_is_naive_and_still_comparable(self, tmp_path: Path) -> None:
        """Regression test for the timezone bug: writing a load with an aware `datetime.now(UTC)`
        and reading it back from the DB (as SQLite does, without tzinfo) must not raise a
        TypeError when checked for staleness."""
        service, local_launcher = _build_launcher_service_with_real_local_launcher(tmp_path)
        local_launcher.submitted_jobs["job-1"] = LauncherParametersDTO(nb_cpu=1)

        result = save_launcher_cache_task.run.__wrapped__(_FakeBoundTask(service))
        assert result.status == BackGroundTaskStatus.SUCCESS

        stored_load = service.launcher_cache_repository.get_launcher_load("local")
        assert stored_load is not None
        # SQLite does not persist tzinfo: this must be naive, not aware, and this must not
        # be an issue for the caller.
        assert stored_load.date.tzinfo is None

        # Must not raise TypeError("can't compare offset-naive and offset-aware datetimes").
        assert service._is_outdated_load_data(stored_load) is False

    @with_db_context
    def test_stale_naive_date_is_correctly_reported_as_outdated(self, tmp_path: Path) -> None:
        service, _ = _build_launcher_service_with_real_local_launcher(tmp_path)

        from antarest.launcher.model import LauncherCache

        stale_naive_load = LauncherCache(
            launcher_name="local",
            allocated_cpu_rate=0,
            cluster_load_rate=0,
            nb_queued_jobs=0,
            launcher_status="SUCCESS",
            date=datetime.now(UTC) - timedelta(days=1),
        )
        service.launcher_cache_repository.update_all_launcher_loads([stale_naive_load])

        stored_load = service.launcher_cache_repository.get_launcher_load("local")
        assert stored_load is not None
        assert stored_load.date.tzinfo is None
        assert service._is_outdated_load_data(stored_load) is True

    @with_db_context
    def test_local_launcher_load_is_still_stale_across_separate_service_instances(self, tmp_path: Path) -> None:
        """This is the regression test for the bug that reusing a single LauncherService
        instance per worker process does NOT fix: in production, the celery worker process
        builds its own `Services.launcher` in `worker_init`, entirely separate from the
        `Services.launcher` living in the web/API process where jobs are actually submitted.
        `LocalLauncher.submitted_jobs` is in-memory, per-process state, so the worker's view
        of the local launcher's load remains 0 regardless of real activity elsewhere."""
        web_process_service, web_process_local_launcher = _build_launcher_service_with_real_local_launcher(tmp_path)
        worker_process_service, _ = _build_launcher_service_with_real_local_launcher(tmp_path)

        # Real activity happens in the "web process" instance only.
        web_process_local_launcher.submitted_jobs["job-1"] = LauncherParametersDTO(nb_cpu=4)
        live_load_in_web_process = web_process_service.get_load("local")
        assert live_load_in_web_process.allocated_cpu_rate > 0

        # The celery task, running with the "worker process" instance, has no visibility
        # into that in-memory state.
        save_launcher_cache_task.run.__wrapped__(_FakeBoundTask(worker_process_service))

        cached_load = worker_process_service.launcher_cache_repository.get_launcher_load("local")
        assert cached_load is not None
        # Bug still present: the persisted cache does not reflect the real load from the
        # web process, and a client reading through this cache (once fresh) would get 0.
        assert cached_load.allocated_cpu_rate == 0

    @with_db_context
    def test_returns_partial_success_when_one_launcher_fails(self, tmp_path: Path) -> None:
        config = Config(
            storage=StorageConfig(tmp_dir=tmp_path),
            launcher=LauncherConfig(default="local", configs=[LocalConfig(id="local", name="name")]),
        )

        ok_launcher = LocalLauncher(
            LocalConfig(id="local", name="name"),
            callbacks=Mock(),
            event_bus=Mock(),
            cache=Mock(),  # type: ignore[union-attr]
        )
        failing_launcher = Mock()
        failing_launcher.get_load.side_effect = SlurmError("unreachable")

        factory_launcher_mock = Mock()
        factory_launcher_mock.build_launcher.return_value = {"local": ok_launcher, "slurm": failing_launcher}

        service = LauncherService(
            config=config,
            study_service=Mock(),
            output_service=Mock(),
            login_service=Mock(),
            job_result_repository=Mock(),
            solver_presets_repository=Mock(),
            launcher_cache_repository=LauncherCacheRepository(),
            event_bus=Mock(),
            factory_launcher=factory_launcher_mock,
            file_transfer_manager=Mock(),
            task_service=Mock(),
            cache=Mock(),
        )

        result = save_launcher_cache_task.run.__wrapped__(_FakeBoundTask(service))

        assert result.status == BackGroundTaskStatus.PARTIAL_SUCCESS
        assert service.launcher_cache_repository.get_launcher_load("local") is not None
        assert service.launcher_cache_repository.get_launcher_load("slurm") is None

    @with_db_context
    def test_returns_success_when_all_launchers_succeed(self, tmp_path: Path) -> None:
        service, local_launcher = _build_launcher_service_with_real_local_launcher(tmp_path)

        result = save_launcher_cache_task.run.__wrapped__(_FakeBoundTask(service))

        assert result.status == BackGroundTaskStatus.SUCCESS


class _FakeBoundTask:
    """Minimal stand-in for the celery `MaintenanceTask` bound instance (`self`), exposing
    only the `context.services.launcher` attribute path the task under test reads."""

    def __init__(self, launcher_service: LauncherService) -> None:
        self.context = Mock(services=Mock(launcher=launcher_service))


def test_raises_without_context(with_no_maintenance_ctx: None) -> None:
    import pytest

    from antarest.maintenance.tasks.common import MaintenanceContextNotFoundError

    with pytest.raises(MaintenanceContextNotFoundError):
        save_launcher_cache_task.run()
