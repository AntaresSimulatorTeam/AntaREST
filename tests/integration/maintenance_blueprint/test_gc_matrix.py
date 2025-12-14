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

"""Integration tests for the matrix garbage collection task."""

from datetime import timedelta

import pandas as pd

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.gc_matrix import (
    GCTaskResult,
    TaskStatus,
    clean_matrices,
)
from antarest.matrixstore.service import MatrixService


class TestCleanMatricesIntegration:
    """Integration tests for clean_matrices using real database and services."""

    def test_deletes_old_unused_matrices(self, matrix_service: MatrixService):
        """Test that old unused matrices are deleted."""
        # Create a matrix
        matrix_data = pd.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)

            # Verify matrix exists
            matrices_before = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_before)

            # Artificially age the matrix by modifying its created_at
            matrix_obj = matrix_service.repo.get(matrix_id)
            assert matrix_obj is not None
            matrix_obj.created_at = current_time() - timedelta(hours=2)
            db.session.commit()

        # Run GC with explicit arguments (no context needed)
        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=False,
            retention_time=3600,  # 1 hour
        )

        # Verify result
        assert isinstance(result, GCTaskResult)
        assert result.status == TaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is False

        # Verify matrix was deleted
        with db():
            matrices_after = matrix_service.get_matrices()
            assert not any(m.id == matrix_id for m in matrices_after)

    def test_keeps_recent_unused_matrices(self, matrix_service: MatrixService):
        """Test that recent unused matrices are NOT deleted."""
        # Create a matrix (will be recent by default)
        matrix_data = pd.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)

        # Run GC
        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=False,
            retention_time=3600,
        )

        # Verify result
        assert result.status == TaskStatus.SUCCESS
        assert result.deleted_count == 0

        # Verify matrix still exists
        with db():
            matrices_after = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_after)

    def test_dry_run_does_not_delete(self, matrix_service: MatrixService):
        """Test that dry_run mode does not delete matrices."""
        # Create and age a matrix
        matrix_data = pd.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)

            # Age the matrix
            matrix_obj = matrix_service.repo.get(matrix_id)
            assert matrix_obj is not None
            matrix_obj.created_at = current_time() - timedelta(hours=2)
            db.session.commit()

        # Run GC with dry_run=True
        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=True,
            retention_time=3600,
        )

        # Verify result indicates deletion would happen
        assert result.status == TaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is True

        # Verify matrix still exists (dry run)
        with db():
            matrices_after = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_after)

    def test_returns_success_with_no_matrices(self, matrix_service: MatrixService):
        """Test successful execution when there are no matrices."""
        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=False,
            retention_time=3600,
        )

        assert result.status == TaskStatus.SUCCESS
        assert result.deleted_count == 0
        assert result.duration_seconds >= 0
