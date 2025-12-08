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
