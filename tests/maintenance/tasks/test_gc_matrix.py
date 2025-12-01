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

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from antarest.maintenance.tasks.gc_matrix import (
    _delete_unused_saved_matrices,
    clean_matrices_task,
)
from antarest.matrixstore.model import MatrixMetadataDTO, MatrixReference


class TestDeleteUnusedSavedMatrices:
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


class TestCleanMatricesTask:
    @pytest.fixture
    def mock_context(self):
        """Create a mock MaintenanceContext."""
        with patch("antarest.maintenance.tasks.gc_matrix.MaintenanceContext") as mock_ctx_class:
            mock_ctx = Mock()
            mock_ctx_class.get_instance.return_value = mock_ctx

            mock_config = Mock()
            mock_config.storage.matrix_gc_dry_run = False
            mock_config.storage.matrix_gc_retention_time = 3600
            mock_ctx.config = mock_config

            mock_matrix_service = Mock()
            mock_ctx.matrix_service = mock_matrix_service

            yield mock_ctx

    @pytest.fixture
    def mock_db(self):
        """Create a mock db context manager."""
        with patch("antarest.maintenance.tasks.gc_matrix.db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__ = Mock(return_value=None)
            mock_db.return_value.__exit__ = Mock(return_value=None)
            mock_db.session = mock_session
            yield mock_db

    def test_returns_skipped_when_lock_not_acquired(self, mock_context, mock_db):
        """Test that task returns 'skipped' status when advisory lock cannot be acquired."""
        # Simulate lock not acquired
        mock_result = Mock()
        mock_result.scalar.return_value = False
        mock_db.session.execute.return_value = mock_result

        result = clean_matrices_task()

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_not_acquired"
        assert result["deleted_count"] == 0
        assert "duration_seconds" in result

    def test_returns_success_with_no_matrices_to_delete(self, mock_context, mock_db):
        """Test successful execution when there are no matrices to delete."""
        # Simulate lock acquired
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_db.session.execute.return_value = mock_result

        # No matrices exist
        mock_context.matrix_service.get_used_matrices.return_value = []
        mock_context.matrix_service.get_matrices.return_value = []

        result = clean_matrices_task()

        assert result["status"] == "success"
        assert result["deleted_count"] == 0
        assert result["dry_run"] is False
        assert "duration_seconds" in result

    @patch("antarest.maintenance.tasks.gc_matrix.current_time")
    def test_deletes_old_unused_matrices(self, mock_current_time, mock_context, mock_db):
        """Test that old unused matrices are deleted."""
        # Simulate lock acquired
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_db.session.execute.return_value = mock_result

        # Set current time
        now = datetime(2025, 1, 1, 12, 0, 0)
        mock_current_time.return_value = now

        # Set retention time to 1 hour
        mock_context.config.storage.matrix_gc_retention_time = 3600

        # Create matrices - one used, two unused (one old, one recent)
        old_time = now - timedelta(hours=2)  # 2 hours old - should be deleted
        recent_time = now - timedelta(minutes=30)  # 30 min old - should NOT be deleted

        mock_context.matrix_service.get_used_matrices.return_value = [
            MatrixReference(matrix_id="used_matrix", use_description="in use")
        ]
        mock_context.matrix_service.get_matrices.return_value = [
            MatrixMetadataDTO(id="used_matrix", width=10, height=10, version=1, created_at=old_time),
            MatrixMetadataDTO(id="old_unused", width=10, height=10, version=1, created_at=old_time),
            MatrixMetadataDTO(id="recent_unused", width=10, height=10, version=1, created_at=recent_time),
        ]

        result = clean_matrices_task()

        assert result["status"] == "success"
        assert result["deleted_count"] == 1
        mock_context.matrix_service.delete.assert_called_once_with("old_unused")

    @patch("antarest.maintenance.tasks.gc_matrix.current_time")
    def test_respects_dry_run_flag(self, mock_current_time, mock_context, mock_db):
        """Test that dry_run=True prevents actual deletion."""
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_db.session.execute.return_value = mock_result

        now = datetime(2025, 1, 1, 12, 0, 0)
        mock_current_time.return_value = now

        # Enable dry run
        mock_context.config.storage.matrix_gc_dry_run = True
        mock_context.config.storage.matrix_gc_retention_time = 3600

        old_time = now - timedelta(hours=2)
        mock_context.matrix_service.get_used_matrices.return_value = []
        mock_context.matrix_service.get_matrices.return_value = [
            MatrixMetadataDTO(id="old_matrix", width=10, height=10, version=1, created_at=old_time),
        ]

        result = clean_matrices_task()

        assert result["status"] == "success"
        assert result["deleted_count"] == 1
        assert result["dry_run"] is True
        # Matrix should NOT be deleted in dry run mode
        mock_context.matrix_service.delete.assert_not_called()

    def test_returns_error_on_exception(self, mock_context, mock_db):
        """Test that exceptions are caught and returned as error status."""
        mock_db.session.execute.side_effect = Exception("Database connection failed")

        result = clean_matrices_task()

        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        assert result["deleted_count"] == 0
        assert "duration_seconds" in result

    @patch("antarest.maintenance.tasks.gc_matrix.current_time")
    def test_respects_retention_time(self, mock_current_time, mock_context, mock_db):
        """Test that only matrices older than retention_time are deleted."""
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_db.session.execute.return_value = mock_result

        now = datetime(2025, 1, 1, 12, 0, 0)
        mock_current_time.return_value = now

        # Set retention time to 24 hours
        mock_context.config.storage.matrix_gc_retention_time = 86400  # 24 hours

        # All matrices are less than 24 hours old
        time_12h_ago = now - timedelta(hours=12)
        mock_context.matrix_service.get_used_matrices.return_value = []
        mock_context.matrix_service.get_matrices.return_value = [
            MatrixMetadataDTO(id="matrix1", width=10, height=10, version=1, created_at=time_12h_ago),
            MatrixMetadataDTO(id="matrix2", width=10, height=10, version=1, created_at=time_12h_ago),
        ]

        result = clean_matrices_task()

        assert result["status"] == "success"
        assert result["deleted_count"] == 0
        mock_context.matrix_service.delete.assert_not_called()
