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

"""Tests for the matrix garbage collection Celery task."""

from unittest.mock import Mock

import pytest

from antarest.maintenance.tasks.gc_matrix import _delete_unused_saved_matrices
from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task


class TestDeleteUnusedSavedMatrices:
    """Unit tests for _delete_unused_saved_matrices helper function."""

    def test_deletes_matrices_when_not_dry_run(self):
        """Test that matrices are deleted when dry_run is False."""
        mock_matrix_service = Mock()
        unused_matrices = {"matrix1", "matrix2", "matrix3"}

        _delete_unused_saved_matrices(
            matrix_service=mock_matrix_service,
            unused_matrices=unused_matrices,
            dry_run=False,
        )

        assert mock_matrix_service.delete.call_count == 3
        mock_matrix_service.delete.assert_any_call("matrix1")
        mock_matrix_service.delete.assert_any_call("matrix2")
        mock_matrix_service.delete.assert_any_call("matrix3")

    def test_does_not_delete_matrices_when_dry_run(self):
        """Test that matrices are NOT deleted when dry_run is True."""
        mock_matrix_service = Mock()
        unused_matrices = {"matrix1", "matrix2"}

        _delete_unused_saved_matrices(
            matrix_service=mock_matrix_service,
            unused_matrices=unused_matrices,
            dry_run=True,
        )

        mock_matrix_service.delete.assert_not_called()

    def test_handles_empty_set(self):
        """Test that empty set of matrices is handled correctly."""
        mock_matrix_service = Mock()

        _delete_unused_saved_matrices(
            matrix_service=mock_matrix_service,
            unused_matrices=set(),
            dry_run=False,
        )

        mock_matrix_service.delete.assert_not_called()


class TestCleanMatricesTaskWiring:
    """Tests for the Celery task wiring (context extraction)."""

    def test_raises_when_config_not_initialized(self):
        """Test that clean_matrices_task raises when config is None."""

        with pytest.raises(RuntimeError, match="MaintenanceContext config is not initialized"):
            clean_matrices_task()
