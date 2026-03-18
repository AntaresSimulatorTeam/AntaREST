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

from unittest.mock import AsyncMock, Mock

from antarest.maintenance.context import MaintenanceContext


class TestMaintenanceContext:
    def test_constructor_stores_config_and_container(self):
        """Test that constructor properly stores config and container."""
        mock_config = Mock()
        mock_container = Mock()

        ctx = MaintenanceContext(config=mock_config, container=mock_container)

        assert ctx.config is mock_config

    def test_matrix_service_resolves_from_container(self):
        """Test that matrix_service property resolves the service from the container."""
        from antarest.matrixstore.service import MatrixService

        mock_matrix_service = Mock(spec=MatrixService)
        mock_container = AsyncMock()
        mock_container.get = AsyncMock(return_value=mock_matrix_service)
        mock_config = Mock()

        ctx = MaintenanceContext(config=mock_config, container=mock_container)

        result = ctx.matrix_service
        assert result is mock_matrix_service
        mock_container.get.assert_called_once_with(MatrixService)

    def test_blob_service_resolves_from_container(self):
        """Test that blob_service property resolves the service from the container."""
        from antarest.blobstore.service import BlobService

        mock_blob_service = Mock(spec=BlobService)
        mock_container = AsyncMock()
        mock_container.get = AsyncMock(return_value=mock_blob_service)
        mock_config = Mock()

        ctx = MaintenanceContext(config=mock_config, container=mock_container)

        result = ctx.blob_service
        assert result is mock_blob_service
        mock_container.get.assert_called_once_with(BlobService)

    def test_multiple_instances_are_independent(self):
        """Test that multiple MaintenanceContext instances are independent (not singleton)."""
        mock_config_1 = Mock()
        mock_config_2 = Mock()
        mock_container_1 = Mock()
        mock_container_2 = Mock()

        ctx1 = MaintenanceContext(config=mock_config_1, container=mock_container_1)
        ctx2 = MaintenanceContext(config=mock_config_2, container=mock_container_2)

        assert ctx1 is not ctx2
        assert ctx1.config is mock_config_1
        assert ctx2.config is mock_config_2
