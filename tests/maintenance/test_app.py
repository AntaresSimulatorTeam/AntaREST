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

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import pytest

from antarest.core.config import Config
from antarest.core.exceptions import ConfigurationError
from antarest.maintenance.app import _mask_url_credentials, _setup_periodic_tasks, celery_app
from antarest.maintenance.config import get_config, load_config


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


@contextmanager
def env_var(name: str, value: str) -> Iterator[None]:
    prev_value = os.environ.get(name)
    os.environ[name] = value
    yield
    if prev_value is None:
        del os.environ[name]
    else:
        os.environ[name] = prev_value


class TestLoadConfig:
    def test_load_config_without_env_var_raises(self, tmp_path: Path):
        with pytest.raises(ConfigurationError):
            load_config()

        with env_var("ANTAREST_CONF", str(tmp_path / "config.yml")):
            with pytest.raises(ConfigurationError):
                load_config()

    def test_load_config_from_file(self, tmp_path: Path):
        Path(tmp_path / "config.yml").write_text("storage: {matrix_gc_sleeping_time: 5432}")
        with env_var("ANTAREST_CONF", str(tmp_path / "config.yml")):
            load_config()
        assert isinstance(get_config(), Config)
        assert get_config().storage.matrix_gc_sleeping_time == 5432


class TestSetupPeriodicTasks:
    def test_uses_config_intervals(self):
        sender = Mock()
        config = Mock()
        config.storage.matrix_gc_sleeping_time = 7200
        config.storage.blob_gc_sleeping_time = 43200
        config.storage.auto_archive_sleeping_time = 1800
        config.storage.auto_archive_cron = None
        config.storage.watcher_scan_sleeping_time = 120
        config.storage.tasks_gc_sleeping_time = 3600
        config.storage.disk_usage_log_sleeping_time = 300
        config.storage.disk_usage_log_cron = None
        config.storage.disk_space_analyzer_sleeping_time = 300
        config.storage.disk_space_analyzer_cron = None

        with mock.patch("antarest.maintenance.app.get_config", return_value=config):
            _setup_periodic_tasks(sender=sender)

        calls = sender.add_periodic_task.call_args_list
        assert calls[0][0][0] == 7200
        assert calls[1][0][0] == 43200
        assert calls[2][0][0] == 1800
        assert calls[3][0][0] == 120
        assert calls[5][0][0] == 3600

        names = [c[1]["name"] for c in calls]
        assert names == [
            "matrices_cleaner",
            "blobs_cleaner",
            "auto_archiver",
            "watcher_scan",
            "variable_view_cleaner",
            "tasks_cleaner",
            "disk_usage",
            "disk_space_analyzer",
            "launcher_load",
        ]
