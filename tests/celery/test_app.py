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

from antarest.celery.app import _mask_url_credentials


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
        with patch("antarest.celery.app._load_config", return_value=None):
            yield

    def test_celery_app_has_correct_name(self, mock_config_loading):
        """Test that the Celery app is created with the correct name."""
        # Import after mock is set up
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.main == "antarest-maintenance"

    def test_celery_app_has_json_serialization(self, mock_config_loading):
        """Test that JSON serialization is configured."""
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.task_serializer == "json"
        assert app_module.celery_app.conf.result_serializer == "json"
        assert "json" in app_module.celery_app.conf.accept_content

    def test_celery_app_has_task_routing(self, mock_config_loading):
        """Test that task routing is configured for maintenance queue."""
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert "antarest.maintenance.tasks.*" in app_module.celery_app.conf.task_routes
        assert app_module.celery_app.conf.task_routes["antarest.maintenance.tasks.*"]["queue"] == "maintenance"

    def test_celery_app_has_timeouts_configured(self, mock_config_loading):
        """Test that task timeouts are configured."""
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.task_soft_time_limit == 7000
        assert app_module.celery_app.conf.task_time_limit == 7200

    def test_celery_app_has_worker_settings(self, mock_config_loading):
        """Test that worker settings are configured."""
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.worker_prefetch_multiplier == 1
        assert app_module.celery_app.conf.worker_max_tasks_per_child == 100
        assert app_module.celery_app.conf.task_acks_late is True
        assert app_module.celery_app.conf.task_reject_on_worker_lost is True

    def test_celery_app_uses_utc(self, mock_config_loading):
        """Test that UTC timezone is enabled."""
        import importlib

        import antarest.celery.app as app_module

        importlib.reload(app_module)

        assert app_module.celery_app.conf.enable_utc is True


class TestInitWorker:
    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset MaintenanceContext singleton before each test."""
        from antarest.celery.context import MaintenanceContext

        MaintenanceContext._instance = None
        yield
        MaintenanceContext._instance = None

    def test_init_worker_returns_early_without_config(self):
        """Test that init_worker returns early when _config is None."""
        from antarest.celery.context import MaintenanceContext

        with patch("antarest.celery.app._config", None):
            from antarest.celery.app import init_worker

            init_worker()

            # Context should not be initialized
            ctx = MaintenanceContext.get_instance()
            assert ctx._initialized is False

    @patch("antarest.celery.app.MaintenanceContext")
    def test_init_worker_initializes_context(self, mock_ctx_class, tmp_path):
        """Test that init_worker properly initializes the MaintenanceContext."""
        # Create a mock config
        mock_config = Mock()
        mock_config.celery = Mock()

        mock_ctx = Mock()
        mock_ctx_class.get_instance.return_value = mock_ctx

        config_file = tmp_path / "application.yaml"
        config_file.write_text("debug: false\n")

        with (
            patch("antarest.celery.app._config", mock_config),
            patch.dict(os.environ, {"ANTAREST_CONF": str(config_file)}),
        ):
            from antarest.celery.app import init_worker

            init_worker()

        mock_ctx.initialize.assert_called_once_with(mock_config, config_file)


class TestSetupPeriodicTasks:
    def test_setup_periodic_tasks_adds_matrix_gc_with_default_interval(self):
        """Test that setup_periodic_tasks registers the matrix GC task with default interval."""
        mock_sender = Mock()

        # When _config is None, use default interval of 3600
        with patch("antarest.celery.app._config", None):
            from antarest.celery.app import setup_periodic_tasks

            setup_periodic_tasks(mock_sender)

        # Verify add_periodic_task was called with correct arguments
        mock_sender.add_periodic_task.assert_called_once()
        call_args = mock_sender.add_periodic_task.call_args
        assert call_args[0][0] == 3600  # default interval
        assert call_args[1]["name"] == "matrix-gc"

    def test_setup_periodic_tasks_uses_interval_from_config(self):
        """Test that setup_periodic_tasks uses interval from config."""
        mock_sender = Mock()

        # Create mock config with custom interval
        mock_celery_config = Mock()
        mock_celery_config.matrix_gc_interval = 7200

        mock_config = Mock()
        mock_config.celery = mock_celery_config

        with patch("antarest.celery.app._config", mock_config):
            from antarest.celery.app import setup_periodic_tasks

            setup_periodic_tasks(mock_sender)

        # Verify add_periodic_task was called with custom interval
        mock_sender.add_periodic_task.assert_called_once()
        call_args = mock_sender.add_periodic_task.call_args
        assert call_args[0][0] == 7200  # custom interval from config
        assert call_args[1]["name"] == "matrix-gc"
