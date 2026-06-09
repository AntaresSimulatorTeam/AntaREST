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

"""Integration tests for the matrix garbage collection task."""

import tempfile
from datetime import timedelta
from pathlib import Path

import polars as pl

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus, GarbageCollectorTaskResult
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.matrixstore.service import MatrixService


class TestCleanMatricesIntegration:
    """Integration tests for clean_matrices using real database and services."""

    def test_deletes_old_unused_matrices(self, matrix_service: MatrixService):
        """Test that old unused matrices are deleted."""
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)
            matrices_before = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_before)

            # Age the matrix
            matrix_obj = matrix_service.repo.get(matrix_id)
            assert matrix_obj is not None
            matrix_obj.created_at = current_time() - timedelta(hours=2)
            db.session.commit()

        result = clean_matrices(
            matrix_service=matrix_service, dry_run=False, retention_time=3600, lock_folder=Path(tempfile.gettempdir())
        )

        assert isinstance(result, GarbageCollectorTaskResult)
        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is False

        with db():
            matrices_after = matrix_service.get_matrices()
            assert not any(m.id == matrix_id for m in matrices_after)

    def test_keeps_recent_unused_matrices(self, matrix_service: MatrixService):
        """Test that recent unused matrices are NOT deleted."""
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)

        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=False,
            retention_time=3600,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 0

        with db():
            matrices_after = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_after)

    def test_dry_run_does_not_delete(self, matrix_service: MatrixService):
        """Test that dry_run mode does not delete matrices."""
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)

            # Age the matrix
            matrix_obj = matrix_service.repo.get(matrix_id)
            assert matrix_obj is not None
            matrix_obj.created_at = current_time() - timedelta(hours=2)
            db.session.commit()

        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=True,
            retention_time=3600,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is True

        with db():
            matrices_after = matrix_service.get_matrices()
            assert any(m.id == matrix_id for m in matrices_after)

    def test_returns_success_with_no_matrices(self, matrix_service: MatrixService):
        """Test successful execution when there are no matrices."""
        result = clean_matrices(
            matrix_service=matrix_service,
            dry_run=False,
            retention_time=3600,
            lock_folder=Path(tempfile.gettempdir()),
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 0
        assert result.duration_seconds >= 0
