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

"""Tests for MaintenanceContext singleton."""

import threading
from unittest.mock import Mock, patch

import pytest

from antarest.maintenance.context import MaintenanceContext


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance before and after each test."""
    MaintenanceContext._INSTANCE = None
    yield
    MaintenanceContext._INSTANCE = None


class TestMaintenanceContext:
    def test_get_instance_returns_singleton(self):
        """Test that get_instance always returns the same instance."""
        instance1 = MaintenanceContext.get_instance()
        instance2 = MaintenanceContext.get_instance()

        assert instance1 is instance2

    def test_get_instance_thread_safe(self):
        """Test that get_instance is thread-safe."""
        instances = []
        errors = []

        def get_instance():
            try:
                instances.append(MaintenanceContext.get_instance())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(instances) == 10
        # All instances should be the same object
        assert all(inst is instances[0] for inst in instances)

    def test_initial_state(self):
        """Test that a new instance is not initialized."""
        ctx = MaintenanceContext.get_instance()

        assert ctx.config is None
        assert ctx.core_services is None
        assert ctx._initialized is False

    def test_matrix_service_raises_when_not_initialized(self):
        """Test that accessing matrix_service before initialization raises RuntimeError."""
        ctx = MaintenanceContext.get_instance()

        with pytest.raises(RuntimeError, match="MaintenanceContext not initialized"):
            _ = ctx.matrix_service

    def test_blob_service_raises_when_not_initialized(self):
        """Test that accessing blob_service before initialization raises RuntimeError."""
        ctx = MaintenanceContext.get_instance()

        with pytest.raises(RuntimeError, match="MaintenanceContext not initialized"):
            _ = ctx.blob_service

    def test_matrix_service_returns_service_when_initialized(self):
        """Test that matrix_service returns the service when context is initialized."""
        ctx = MaintenanceContext.get_instance()

        # Manually set up initialized state with mocks
        mock_matrix_service = Mock()
        mock_core_services = Mock()
        mock_core_services.matrix_service = mock_matrix_service

        ctx._initialized = True
        ctx.core_services = mock_core_services

        assert ctx.matrix_service is mock_matrix_service

    def test_blob_service_returns_service_when_initialized(self):
        """Test that blob_service returns the service when context is initialized."""
        ctx = MaintenanceContext.get_instance()

        # Manually set up initialized state with mocks
        mock_blob_service = Mock()
        mock_core_services = Mock()
        mock_core_services.blob_service = mock_blob_service

        ctx._initialized = True
        ctx.core_services = mock_core_services

        assert ctx.blob_service is mock_blob_service

    def test_initialize_skips_if_already_initialized(self):
        """Test that initialize() does nothing if already initialized."""
        from pathlib import Path

        ctx = MaintenanceContext.get_instance()
        ctx._initialized = True

        mock_config = Mock()
        # This should not raise any error and should return early
        ctx.initialize(mock_config, Path("/fake/path"))

        # Config should still be None since initialize returned early
        assert ctx.config is None

    @patch("antarest.maintenance.context.init_db_engine")
    @patch("antarest.maintenance.context.DBSessionMiddleware")
    @patch("antarest.maintenance.context.create_core_services")
    def test_initialize_creates_services(
        self,
        mock_create_core_services,
        mock_db_middleware,
        mock_init_db_engine,
        tmp_path,
    ):
        """Test that initialize() properly creates config and services."""
        # Setup mocks
        mock_config = Mock()
        mock_core_services = Mock()
        mock_create_core_services.return_value = mock_core_services

        # Create a fake config file
        config_path = tmp_path / "application.yaml"
        config_path.touch()

        ctx = MaintenanceContext.get_instance()
        ctx.initialize(mock_config, config_path)

        assert ctx._initialized is True
        assert ctx.config is mock_config
        assert ctx.core_services is mock_core_services
        mock_create_core_services.assert_called_once_with(app_ctxt=None, config=mock_config)

    @patch("antarest.maintenance.context.init_db_engine")
    @patch("antarest.maintenance.context.DBSessionMiddleware")
    @patch("antarest.maintenance.context.create_core_services")
    def test_initialize_is_idempotent(
        self,
        mock_create_core_services,
        mock_db_middleware,
        mock_init_db_engine,
        tmp_path,
    ):
        """Test that calling initialize() multiple times only initializes once."""
        mock_config = Mock()
        mock_core_services = Mock()
        mock_create_core_services.return_value = mock_core_services

        config_path = tmp_path / "application.yaml"
        config_path.touch()

        ctx = MaintenanceContext.get_instance()
        ctx.initialize(mock_config, config_path)
        ctx.initialize(mock_config, config_path)
        ctx.initialize(mock_config, config_path)

        # Should only be called once
        assert mock_create_core_services.call_count == 1
