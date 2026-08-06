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

"""Tests for MaintenanceContext."""

from unittest.mock import Mock

from antarest.maintenance.context import MaintenanceContext


class TestMaintenanceContext:
    def test_constructor_stores_config_and_services(self):
        """Test that constructor properly stores config and core_services."""
        mock_config = Mock()
        mock_core_services = Mock()

        ctx = MaintenanceContext(config=mock_config, core_services=mock_core_services)

        assert ctx.config is mock_config
        assert ctx.core_services is mock_core_services

    def test_matrix_service_returns_service_from_core_services(self):
        """Test that matrix_service property returns the service from core_services."""
        mock_matrix_service = Mock()
        mock_core_services = Mock()
        mock_core_services.matrix_service = mock_matrix_service
        mock_config = Mock()

        ctx = MaintenanceContext(config=mock_config, core_services=mock_core_services)

        assert ctx.matrix_service is mock_matrix_service

    def test_blob_service_returns_service_from_core_services(self):
        """Test that blob_service property returns the service from core_services."""
        mock_blob_service = Mock()
        mock_core_services = Mock()
        mock_core_services.blob_service = mock_blob_service
        mock_config = Mock()

        ctx = MaintenanceContext(config=mock_config, core_services=mock_core_services)

        assert ctx.blob_service is mock_blob_service

    def test_multiple_instances_are_independent(self):
        """Test that multiple MaintenanceContext instances are independent (not singleton)."""
        mock_config_1 = Mock()
        mock_config_2 = Mock()
        mock_core_services_1 = Mock()
        mock_core_services_2 = Mock()

        ctx1 = MaintenanceContext(config=mock_config_1, core_services=mock_core_services_1)
        ctx2 = MaintenanceContext(config=mock_config_2, core_services=mock_core_services_2)

        assert ctx1 is not ctx2
        assert ctx1.config is mock_config_1
        assert ctx2.config is mock_config_2
