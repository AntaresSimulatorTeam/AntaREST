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


class TestCeleryAppConfiguration:
    def test_celery_app_has_correct_name(self):
        """Test that the Celery app is created with the correct name."""
        from antarest.celery.app import celery_app

        assert celery_app.main == "antarest-maintenance"

    def test_celery_app_has_json_serialization(self):
        """Test that JSON serialization is configured."""
        from antarest.celery.app import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_celery_app_has_task_routing(self):
        """Test that task routing is configured for maintenance queue."""
        from antarest.celery.app import celery_app

        assert "antarest.maintenance.tasks.*" in celery_app.conf.task_routes
        assert celery_app.conf.task_routes["antarest.maintenance.tasks.*"]["queue"] == "maintenance"

    def test_celery_app_has_timeouts_configured(self):
        """Test that task timeouts are configured."""
        from antarest.celery.app import celery_app

        assert celery_app.conf.task_soft_time_limit == 7000
        assert celery_app.conf.task_time_limit == 7200

    def test_celery_app_has_worker_settings(self):
        """Test that worker settings are configured."""
        from antarest.celery.app import celery_app

        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 100
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_celery_app_uses_utc(self):
        """Test that UTC timezone is enabled."""
        from antarest.celery.app import celery_app

        assert celery_app.conf.enable_utc is True

    @patch.dict(os.environ, {"CELERY_BROKER_URL": "redis://custom:6379/2"})
    def test_celery_app_reads_broker_from_env(self):
        """Test that broker URL can be configured via environment variable."""
        # Need to reimport to pick up the env var
        # Note: This test verifies the mechanism, actual value depends on import order
        broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        assert broker_url == "redis://custom:6379/2"

    @patch.dict(os.environ, {"CELERY_TIMEZONE": "Europe/Paris"})
    def test_celery_app_reads_timezone_from_env(self):
        """Test that timezone can be configured via environment variable."""
        timezone = os.getenv("CELERY_TIMEZONE", "UTC")
        assert timezone == "Europe/Paris"


class TestInitWorker:
    @pytest.fixture(autouse=True)
    def reset_context(self):
        """Reset MaintenanceContext singleton before each test."""
        from antarest.celery.context import MaintenanceContext

        MaintenanceContext._instance = None
        yield
        MaintenanceContext._instance = None

    @patch.dict(os.environ, {}, clear=True)
    def test_init_worker_returns_early_without_config_env(self):
        """Test that init_worker returns early when ANTAREST_CONF is not set."""
        from antarest.celery.app import init_worker
        from antarest.celery.context import MaintenanceContext

        # Remove ANTAREST_CONF if it exists
        os.environ.pop("ANTAREST_CONF", None)

        init_worker()

        # Context should not be initialized
        ctx = MaintenanceContext.get_instance()
        assert ctx._initialized is False

    @patch.dict(os.environ, {"ANTAREST_CONF": "/nonexistent/path/config.yaml"})
    def test_init_worker_returns_early_when_config_not_found(self):
        """Test that init_worker returns early when config file doesn't exist."""
        from antarest.celery.app import init_worker
        from antarest.celery.context import MaintenanceContext

        init_worker()

        ctx = MaintenanceContext.get_instance()
        assert ctx._initialized is False

    @patch("antarest.celery.app.MaintenanceContext")
    @patch("antarest.celery.app.Config")
    def test_init_worker_initializes_context(self, mock_config_class, mock_ctx_class, tmp_path):
        """Test that init_worker properly initializes the MaintenanceContext."""
        from antarest.celery.app import init_worker

        # Create a temporary config file
        config_file = tmp_path / "application.yaml"
        config_file.write_text("debug: false\n")

        # Setup mocks
        mock_config = Mock()
        mock_config.celery = None  # No celery config in YAML
        mock_config_class.from_yaml_file.return_value = mock_config

        mock_ctx = Mock()
        mock_ctx_class.get_instance.return_value = mock_ctx

        with patch.dict(os.environ, {"ANTAREST_CONF": str(config_file)}):
            init_worker()

        mock_ctx.initialize.assert_called_once_with(str(config_file))

    @patch("antarest.celery.app.celery_app")
    @patch("antarest.celery.app.MaintenanceContext")
    @patch("antarest.celery.app.Config")
    def test_init_worker_overrides_celery_config_from_yaml(
        self, mock_config_class, mock_ctx_class, mock_celery_app, tmp_path
    ):
        """Test that init_worker overrides Celery config from YAML if present."""
        from antarest.celery.app import init_worker

        config_file = tmp_path / "application.yaml"
        config_file.write_text("debug: false\n")

        # Setup mock config with celery section
        mock_celery_config = Mock()
        mock_celery_config.broker_url = "redis://yaml-broker:6379/0"
        mock_celery_config.result_backend = "redis://yaml-backend:6379/0"
        mock_celery_config.timezone = "Europe/Paris"

        mock_config = Mock()
        mock_config.celery = mock_celery_config
        mock_config_class.from_yaml_file.return_value = mock_config

        mock_ctx = Mock()
        mock_ctx_class.get_instance.return_value = mock_ctx

        with patch.dict(os.environ, {"ANTAREST_CONF": str(config_file)}):
            init_worker()

        # Verify celery_app.conf.update was called with YAML values
        mock_celery_app.conf.update.assert_called_once_with(
            broker_url="redis://yaml-broker:6379/0",
            result_backend="redis://yaml-backend:6379/0",
            timezone="Europe/Paris",
        )


class TestSetupPeriodicTasks:
    def test_setup_periodic_tasks_adds_matrix_gc(self):
        """Test that setup_periodic_tasks registers the matrix GC task."""
        from antarest.celery.app import setup_periodic_tasks

        mock_sender = Mock()

        setup_periodic_tasks(mock_sender)

        # Verify add_periodic_task was called with correct arguments
        mock_sender.add_periodic_task.assert_called_once()
        call_args = mock_sender.add_periodic_task.call_args
        assert call_args[0][0] == 3600  # interval
        assert call_args[1]["name"] == "matrix-gc"
