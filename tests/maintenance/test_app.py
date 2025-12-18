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

from antarest.maintenance.app import _mask_url_credentials, celery_app


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


class TestCeleryAppStaticConfiguration:
    """
    Tests for static Celery app configuration.

    These tests verify the configuration that is set at module level,
    without any dynamic config loading. No reload() needed since there
    are no side effects at import time.
    """

    def test_celery_app_has_correct_name(self):
        """Test that the Celery app is created with the correct name."""
        assert celery_app.main == "antarest-maintenance"

    def test_celery_app_has_json_serialization(self):
        """Test that JSON serialization is configured."""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_celery_app_has_task_routing(self):
        """Test that task routing is configured for maintenance queue."""
        assert "antarest.maintenance.tasks.*" in celery_app.conf.task_routes
        assert celery_app.conf.task_routes["antarest.maintenance.tasks.*"]["queue"] == "maintenance"

    def test_celery_app_has_timeouts_configured(self):
        """Test that task timeouts are configured."""
        assert celery_app.conf.task_soft_time_limit == 7000
        assert celery_app.conf.task_time_limit == 7200

    def test_celery_app_has_worker_settings(self):
        """Test that worker settings are configured."""
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 100
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_celery_app_uses_utc(self):
        """Test that UTC timezone is enabled."""
        assert celery_app.conf.enable_utc is True


class TestConfigureFromEnvironment:
    """Tests for the _configure_from_environment signal handler."""

    def test_configure_loads_and_stores_config(self):
        """Test that _configure_from_environment loads config and stores it in app.conf."""
        mock_config = Mock()
        mock_config.celery = Mock()
        mock_config.celery.broker_url = "redis://localhost:6379/0"
        mock_config.celery.result_backend = "redis://localhost:6379/0"
        mock_config.celery.result_expires = 3600

        # Save original value to restore later
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            with (
                patch("antarest.maintenance.app._load_config", return_value=mock_config),
                patch("antarest.maintenance.app.configure_logger"),
            ):
                from antarest.maintenance.app import _configure_from_environment

                _configure_from_environment(sender="test-worker", conf=celery_app.conf)

                # Config should be stored in app.conf
                assert celery_app.conf.antarest_config is mock_config
        finally:
            # Restore original value
            celery_app.conf.antarest_config = original_config

    def test_configure_handles_no_config(self):
        """Test that _configure_from_environment handles missing config gracefully."""
        # Save original value to restore later
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            # Set to None explicitly
            celery_app.conf.antarest_config = None

            with patch("antarest.maintenance.app._load_config", return_value=None):
                from antarest.maintenance.app import _configure_from_environment

                # Should not raise
                _configure_from_environment(sender="test-worker", conf=celery_app.conf)

                # Config should still be None
                assert celery_app.conf.antarest_config is None
        finally:
            # Restore original value
            celery_app.conf.antarest_config = original_config


class TestInitWorker:
    """Tests for the _init_worker signal handler."""

    def test_init_worker_does_not_create_context_without_config(self):
        """Test that _init_worker does not create MaintenanceContext when config is not in app.conf."""
        mock_sender = Mock()

        # Save and clear
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            celery_app.conf.antarest_config = None

            with patch("antarest.maintenance.app.MaintenanceContext") as mock_ctx_class:
                from antarest.maintenance.app import _init_worker

                _init_worker(sender=mock_sender)

                # MaintenanceContext.create should NOT have been called
                mock_ctx_class.create.assert_not_called()
        finally:
            celery_app.conf.antarest_config = original_config

    def test_init_worker_does_not_create_context_without_env_var(self):
        """Test that _init_worker does not create MaintenanceContext when ANTAREST_CONF is not set."""
        mock_config = Mock()
        mock_sender = Mock()

        # Save original
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            celery_app.conf.antarest_config = mock_config

            with (
                patch("antarest.maintenance.app.MaintenanceContext") as mock_ctx_class,
                patch.dict(os.environ, {}, clear=True),
            ):
                os.environ.pop("ANTAREST_CONF", None)

                from antarest.maintenance.app import _init_worker

                _init_worker(sender=mock_sender)

                # MaintenanceContext.create should NOT have been called
                mock_ctx_class.create.assert_not_called()
        finally:
            celery_app.conf.antarest_config = original_config

    def test_init_worker_creates_context_and_attaches_to_app(self):
        """Test that _init_worker creates MaintenanceContext and attaches it to app.conf."""
        mock_config = Mock()
        mock_sender = Mock()
        mock_ctx = Mock()

        # Save original
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            celery_app.conf.antarest_config = mock_config

            with (
                patch("antarest.maintenance.app.MaintenanceContext") as mock_ctx_class,
                patch.dict(os.environ, {"ANTAREST_CONF": "/path/to/config.yaml"}),
            ):
                mock_ctx_class.create.return_value = mock_ctx

                from antarest.maintenance.app import _init_worker

                _init_worker(sender=mock_sender)

                # MaintenanceContext.create should have been called with correct args
                mock_ctx_class.create.assert_called_once()
                call_args = mock_ctx_class.create.call_args
                # create(config, config_path) - positional args
                assert call_args[0][0] is mock_config  # First positional arg is config

                # Context should be attached to sender.conf
                assert mock_sender.conf.maintenance_ctx is mock_ctx
        finally:
            celery_app.conf.antarest_config = original_config


class TestSetupPeriodicTasks:
    """Tests for the _setup_periodic_tasks signal handler."""

    def test_setup_periodic_tasks_uses_default_interval_without_config(self):
        """Test that _setup_periodic_tasks uses default interval when no config is available."""
        mock_sender = Mock()

        # Save original
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            celery_app.conf.antarest_config = None

            with patch("antarest.maintenance.tasks.gc_matrix_task.clean_matrices_task") as mock_task:
                mock_task.s.return_value = Mock()
                mock_task.apply_async = Mock()

                from antarest.maintenance.app import _setup_periodic_tasks

                _setup_periodic_tasks(sender=mock_sender)

                # Should use default interval of 3600
                mock_sender.add_periodic_task.assert_called_once()
                call_args = mock_sender.add_periodic_task.call_args
                assert call_args[0][0] == 3600  # Default interval
        finally:
            celery_app.conf.antarest_config = original_config

    def test_setup_periodic_tasks_uses_config_interval(self):
        """Test that _setup_periodic_tasks uses interval from config."""
        mock_sender = Mock()
        mock_config = Mock()
        mock_config.storage.matrix_gc_sleeping_time = 7200  # 2 hours

        # Save original
        original_config = getattr(celery_app.conf, "antarest_config", None)

        try:
            celery_app.conf.antarest_config = mock_config

            with patch("antarest.maintenance.tasks.gc_matrix_task.clean_matrices_task") as mock_task:
                mock_task.s.return_value = Mock()
                mock_task.apply_async = Mock()

                from antarest.maintenance.app import _setup_periodic_tasks

                _setup_periodic_tasks(sender=mock_sender)

                # Should use config interval
                mock_sender.add_periodic_task.assert_called_once()
                call_args = mock_sender.add_periodic_task.call_args
                assert call_args[0][0] == 7200  # Config interval
        finally:
            celery_app.conf.antarest_config = original_config
