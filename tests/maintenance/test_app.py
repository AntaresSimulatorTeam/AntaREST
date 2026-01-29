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

"""Tests for Celery app configuration."""

from unittest.mock import Mock

import pytest

from antarest.maintenance.app import (
    _configure_from_environment,
    _init_worker,
    _mask_url_credentials,
    _setup_periodic_tasks,
    celery_app,
)
from antarest.maintenance.tasks.common import TaskName


class TestMaskUrlCredentials:
    def test_masks_password(self):
        assert _mask_url_credentials("redis://user:secret@localhost:6379/0") == "redis://user:***@localhost:6379/0"

    def test_preserves_url_without_creds(self):
        assert _mask_url_credentials("redis://localhost:6379/0") == "redis://localhost:6379/0"

    def test_masks_special_chars(self):
        masked = _mask_url_credentials("redis://admin:p4ss!w0rd#123@host:6379/1")
        assert "p4ss!w0rd#123" not in masked


class TestCeleryAppConfig:
    def test_app_name(self):
        assert celery_app.main == "antarest-maintenance"

    def test_json_serialization(self):
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_task_routing(self):
        routes = celery_app.conf.task_routes
        assert routes[TaskName.MATRICES_CLEANER]["queue"] == "maintenance"
        assert routes[TaskName.BLOBS_CLEANER]["queue"] == "maintenance"
        assert routes[TaskName.AUTO_ARCHIVER]["queue"] == "maintenance"
        assert routes[TaskName.WATCHER_SCAN]["queue"] == "maintenance"
        assert routes[TaskName.VARIABLE_VIEW_CLEANER]["queue"] == "maintenance"

    def test_timeouts(self):
        assert celery_app.conf.task_soft_time_limit == 7000
        assert celery_app.conf.task_time_limit == 7200

    def test_worker_settings(self):
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.task_acks_late is True


@pytest.fixture
def celery_app_config_backup():
    original_config = getattr(celery_app.conf, "antarest_config", None)
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.antarest_config = original_config
    celery_app.conf.task_always_eager = original_eager


class TestConfigureFromEnvironment:
    def test_stores_config(self, celery_app_config_backup, monkeypatch):
        mock_config = Mock()
        mock_config.celery = Mock(
            broker_url="redis://localhost", result_backend="redis://localhost", result_expires=3600
        )
        monkeypatch.setattr("antarest.maintenance.app._load_config", lambda: mock_config)
        monkeypatch.setattr("antarest.maintenance.app.configure_logger", lambda x: None)

        _configure_from_environment(sender="test", conf=celery_app.conf)
        assert celery_app.conf.antarest_config is mock_config

    def test_handles_no_config(self, celery_app_config_backup, monkeypatch):
        celery_app.conf.antarest_config = None
        monkeypatch.setattr("antarest.maintenance.app._load_config", lambda: None)
        _configure_from_environment(sender="test", conf=celery_app.conf)
        assert celery_app.conf.antarest_config is None


class TestInitWorker:
    def test_no_context_without_config(self, celery_app_config_backup, monkeypatch):
        mock_ctx_class = Mock()
        celery_app.conf.antarest_config = None
        monkeypatch.setattr("antarest.maintenance.app.MaintenanceContext", mock_ctx_class)

        _init_worker(sender=Mock())
        mock_ctx_class.create.assert_not_called()

    def test_no_context_without_env_var(self, celery_app_config_backup, monkeypatch):
        mock_ctx_class = Mock()
        celery_app.conf.antarest_config = Mock()
        monkeypatch.setattr("antarest.maintenance.app.MaintenanceContext", mock_ctx_class)
        monkeypatch.delenv("ANTAREST_CONF", raising=False)

        _init_worker(sender=Mock())
        mock_ctx_class.create.assert_not_called()

    def test_creates_and_attaches_context(self, celery_app_config_backup, monkeypatch):
        mock_ctx = Mock()
        mock_ctx_class = Mock(create=Mock(return_value=mock_ctx))
        mock_sender = Mock()
        celery_app.conf.antarest_config = Mock()

        monkeypatch.setattr("antarest.maintenance.app.MaintenanceContext", mock_ctx_class)
        monkeypatch.setenv("ANTAREST_CONF", "/path/to/config.yaml")

        _init_worker(sender=mock_sender)
        # Context is attached to celery_app.conf, not sender.conf
        assert celery_app.conf.maintenance_ctx is mock_ctx


class TestBeatScheduleConfig:
    """Tests for beat_schedule configuration (defined at module level)."""

    def test_beat_schedule_has_all_tasks(self):
        schedule = celery_app.conf.beat_schedule
        expected_tasks = set(TaskName)
        assert set(schedule.keys()) == expected_tasks

    def test_beat_schedule_task_names_match_keys(self):
        schedule = celery_app.conf.beat_schedule
        for name, config in schedule.items():
            assert config["task"] == name

    def test_beat_schedule_has_schedules(self):
        schedule = celery_app.conf.beat_schedule
        for name, config in schedule.items():
            assert "schedule" in config
            assert isinstance(config["schedule"], (int, float))
            assert config["schedule"] > 0


class TestSetupPeriodicTasks:
    """Tests for initial task triggering on startup."""

    def test_triggers_initial_tasks_with_stagger(self, celery_app_config_backup, monkeypatch):
        mock_matrices = Mock()
        mock_blobs = Mock()
        mock_archive = Mock()
        mock_variable = Mock()
        mock_watcher = Mock()

        # Patch at the source module where the tasks are defined
        monkeypatch.setattr("antarest.maintenance.tasks.gc_matrix_task.clean_matrices_task", mock_matrices)
        monkeypatch.setattr("antarest.maintenance.tasks.gc_blob_task.clean_blobs_task", mock_blobs)
        monkeypatch.setattr("antarest.maintenance.tasks.auto_archive_task.auto_archive_task", mock_archive)
        monkeypatch.setattr("antarest.maintenance.tasks.gc_variable_view_task.clean_variable_views_task", mock_variable)
        monkeypatch.setattr("antarest.maintenance.tasks.watcher_scan_task.watcher_scan_task", mock_watcher)

        _setup_periodic_tasks(sender=Mock())

        mock_matrices.apply_async.assert_called_once_with(countdown=60)
        mock_blobs.apply_async.assert_called_once_with(countdown=90)
        mock_archive.apply_async.assert_called_once_with(countdown=120)
        mock_variable.apply_async.assert_called_once_with(countdown=150)
        mock_watcher.apply_async.assert_called_once_with(countdown=30)
