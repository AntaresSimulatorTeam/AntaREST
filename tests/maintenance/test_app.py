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
    _configure_celery,
    _init_worker,
    _mask_url_credentials,
    _setup_periodic_tasks,
    celery_app,
)


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
        for task_name in [
            "watcher_scan",
            "matrices_cleaner",
            "blobs_cleaner",
            "auto_archiver",
            "variable_view_cleaner",
        ]:
            assert celery_app.conf.task_routes[task_name]["queue"] == "maintenance"

    def test_timeouts(self):
        assert celery_app.conf.task_soft_time_limit == 6600
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

        _configure_celery(sender="test", conf=celery_app.conf)
        assert celery_app.conf.antarest_config is mock_config

    def test_handles_no_config(self, celery_app_config_backup, monkeypatch):
        celery_app.conf.antarest_config = None
        monkeypatch.setattr("antarest.maintenance.app._load_config", lambda: None)
        _configure_celery(sender="test", conf=celery_app.conf)
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


class TestSetupPeriodicTasks:
    def test_uses_defaults_without_config(self, celery_app_config_backup):
        from celery.schedules import crontab

        sender = Mock()
        celery_app.conf.antarest_config = None

        _setup_periodic_tasks(sender=sender)

        assert sender.add_periodic_task.call_count == 5
        calls = sender.add_periodic_task.call_args_list
        assert calls[0][0][0] == 3600  # matrix GC default
        assert calls[1][0][0] == 86400  # blob GC default
        assert isinstance(calls[2][0][0], crontab)
        assert str(calls[2][0][0]) == "<crontab: 0 20-23,0-7 * * * (m/h/dM/MY/d)>"
        assert calls[3][0][0] == 900  # watcher scan default
        assert calls[4][0][0] == 3600  # variable view GC default

    def test_uses_config_intervals(self, celery_app_config_backup):
        sender = Mock()
        config = Mock()
        config.storage.matrix_gc_sleeping_time = 7200
        config.storage.blob_gc_sleeping_time = 43200
        config.storage.auto_archive_sleeping_time = 1800
        config.storage.auto_archive_cron = None
        config.storage.watcher_scan_sleeping_time = 120
        celery_app.conf.antarest_config = config

        _setup_periodic_tasks(sender=sender)

        calls = sender.add_periodic_task.call_args_list
        assert calls[0][0][0] == 7200
        assert calls[1][0][0] == 43200
        assert calls[2][0][0] == 1800
        assert calls[3][0][0] == 120

    def test_task_names(self, celery_app_config_backup):
        sender = Mock()
        celery_app.conf.antarest_config = None

        _setup_periodic_tasks(sender=sender)

        names = [c[1]["name"] for c in sender.add_periodic_task.call_args_list]
        assert names == ["matrices_cleaner", "blobs_cleaner", "auto_archiver", "watcher_scan", "variable_view_cleaner"]
