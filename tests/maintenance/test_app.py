# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

"""Tests for Celery app configuration and initialization."""

import os
from unittest.mock import Mock, patch

import pytest

from antarest.maintenance.app import _mask_url_credentials


class TestMaskUrlCredentials:
    def test_masks_password_in_url(self):
        """Test that password is masked in URL."""
        url = "redis://user:secret_password@localhost:6379/0"
        masked = _mask_url_credentials(url)

        assert masked == "redis://user:***@localhost:6379/0"
        assert "secret_password" not in masked

    def test_preserves_url_without_credentials(self):
        """Test that URL without credentials is unchanged."""
        url = "redis://localhost:6379/0"
        masked = _mask_url_credentials(url)

        assert masked == url

    def test_masks_password_with_special_chars(self):
        """Test that passwords with special chars (except @) are masked."""
        url = "redis://admin:p4ss!w0rd#123@host:6379/1"
        masked = _mask_url_credentials(url)

        assert "p4ss!w0rd#123" not in masked
        assert "***@host" in masked


class TestCeleryAppConfiguration:
    @pytest.fixture(autouse=True)
    def mock_config_loading(self):
        """Mock config loading to avoid needing ANTAREST_CONF."""
        with patch("antarest.maintenance.app._load_config", return_value=None):
            yield

    def test_celery_app_has_correct_name(self, mock_config_loading):
        """Test that the Celery app is created with the correct name."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.main == "antarest-maintenance"

    def test_celery_app_has_json_serialization(self, mock_config_loading):
        """Test that JSON serialization is configured."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.task_serializer == "json"
        assert app_module.celery_app.conf.result_serializer == "json"
        assert "json" in app_module.celery_app.conf.accept_content

    def test_celery_app_has_task_routing(self, mock_config_loading):
        """Test that task routing is configured for maintenance queue."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert "antarest.maintenance.tasks.*" in app_module.celery_app.conf.task_routes
        assert app_module.celery_app.conf.task_routes["antarest.maintenance.tasks.*"]["queue"] == "maintenance"

    def test_celery_app_has_timeouts_configured(self, mock_config_loading):
        """Test that task timeouts are configured."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.task_soft_time_limit == 7000
        assert app_module.celery_app.conf.task_time_limit == 7200

    def test_celery_app_has_worker_settings(self, mock_config_loading):
        """Test that worker settings are configured."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.worker_prefetch_multiplier == 1
        assert app_module.celery_app.conf.worker_max_tasks_per_child == 100
        assert app_module.celery_app.conf.task_acks_late is True
        assert app_module.celery_app.conf.task_reject_on_worker_lost is True

    def test_celery_app_uses_utc(self, mock_config_loading):
        """Test that UTC timezone is enabled."""
        import importlib

        import antarest.maintenance.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.enable_utc is True


class TestInitWorker:
    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset MaintenanceContext singleton before each test."""
        from antarest.maintenance.context import MaintenanceContext

        MaintenanceContext._INSTANCE = None
        yield
        MaintenanceContext._INSTANCE = None

    def test_init_worker_returns_early_without_config(self):
        """Test that init_worker returns early when _config is None."""
        from antarest.maintenance.context import MaintenanceContext

        with patch("antarest.maintenance.app._config", None):
            from antarest.maintenance.app import init_worker

            init_worker()

            ctx = MaintenanceContext.get_instance()
            assert ctx.core_services is None

    def test_init_worker_returns_early_without_env_var(self):
        """Test that init_worker returns early when ANTAREST_CONF is not set."""
        from antarest.maintenance.context import MaintenanceContext

        mock_config = Mock()

        with (
            patch("antarest.maintenance.app._config", mock_config),
            patch.dict(os.environ, {}, clear=True),
        ):
            os.environ.pop("ANTAREST_CONF", None)

            from antarest.maintenance.app import init_worker

            init_worker()

            ctx = MaintenanceContext.get_instance()
            assert ctx.core_services is None
