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

"""Integration tests for the variable view garbage collection task."""

import uuid
from datetime import datetime, timedelta

import polars as pl

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.gc_variable_view import clean_variable_views
from antarest.matrixstore.service import MatrixService
from antarest.output.output_model import OutputVariablesType, OutputVariablesViewsModel
from antarest.study.model import MatrixFrequency, RawStudy


def _create_study(study_id: str) -> RawStudy:
    """Helper to create a minimal study."""
    return RawStudy(
        id=study_id,
        name="Test Study",
        version="8.6",
        path="/tmp/test",
        workspace="default",
    )


def _create_variable_view(
    study_id: str,
    output_id: str,
    matrix_id: str,
    last_read: datetime,
) -> OutputVariablesViewsModel:
    """Helper to create a variable view entry."""
    return OutputVariablesViewsModel(
        id=str(uuid.uuid4()),
        study_id=study_id,
        output_id=output_id,
        type=OutputVariablesType.AREA,
        frequency=MatrixFrequency.WEEKLY,
        variable_name="TEST_VAR",
        area_id="test_area",
        matrix_id=matrix_id,
        last_read=last_read,
    )


class TestCleanVariableViewsIntegration:
    """Integration tests for clean_variable_views using real database."""

    def test_deletes_old_variable_views(self, matrix_service: MatrixService):
        """Test that old variable views are deleted."""
        study_id = str(uuid.uuid4())
        output_id = "test-output"
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)
            db.session.add(_create_study(study_id))
            db.session.flush()
            db.session.add(
                _create_variable_view(
                    study_id=study_id,
                    output_id=output_id,
                    matrix_id=matrix_id,
                    last_read=current_time() - timedelta(days=40),
                )
            )
            db.session.commit()

            views_before = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_before) == 1

        result = clean_variable_views(dry_run=False, retention_time=7)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is False

        with db():
            views_after = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_after) == 0

    def test_keeps_recent_variable_views(self, matrix_service: MatrixService):
        """Test that recent variable views are NOT deleted."""
        study_id = str(uuid.uuid4())
        output_id = "test-output"
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)
            db.session.add(_create_study(study_id))
            db.session.flush()
            db.session.add(
                _create_variable_view(
                    study_id=study_id,
                    output_id=output_id,
                    matrix_id=matrix_id,
                    last_read=current_time() - timedelta(days=1),
                )
            )
            db.session.commit()

        result = clean_variable_views(dry_run=False, retention_time=7)

        assert result.status == BackGroundTaskStatus.SKIPPED
        assert result.reason == "no_unused_variable_view"
        assert result.deleted_count == 0

        with db():
            views_after = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_after) == 1

    def test_dry_run_does_not_delete(self, matrix_service: MatrixService):
        """Test that dry_run mode does not delete variable views."""
        study_id = str(uuid.uuid4())
        output_id = "test-output"
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id = matrix_service.create(matrix_data)
            db.session.add(_create_study(study_id))
            db.session.flush()
            db.session.add(
                _create_variable_view(
                    study_id=study_id,
                    output_id=output_id,
                    matrix_id=matrix_id,
                    last_read=current_time() - timedelta(days=10),
                )
            )
            db.session.commit()

        result = clean_variable_views(dry_run=True, retention_time=7)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is True

        with db():
            views_after = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_after) == 1

    def test_returns_skipped_with_no_views(self):
        """Test execution when there are no variable views."""
        result = clean_variable_views(dry_run=False, retention_time=7)

        assert result.status == BackGroundTaskStatus.SKIPPED
        assert result.reason == "no_unused_variable_view"
        assert result.deleted_count == 0
        assert result.duration_seconds >= 0

    def test_deletes_only_old_views_keeps_recent(self, matrix_service: MatrixService):
        """Test that only old views are deleted while recent ones are kept."""
        study_id = str(uuid.uuid4())
        output_id = "test-output"
        matrix_data = pl.DataFrame([[1, 2], [3, 4]])

        with db():
            matrix_id_old = matrix_service.create(matrix_data)
            matrix_id_recent = matrix_service.create(matrix_data)
            db.session.add(_create_study(study_id))
            db.session.flush()

            # Old view - should be deleted
            db.session.add(
                _create_variable_view(
                    study_id=study_id,
                    output_id=output_id,
                    matrix_id=matrix_id_old,
                    last_read=current_time() - timedelta(days=10),
                )
            )
            # Recent view - should be kept
            db.session.add(
                _create_variable_view(
                    study_id=study_id,
                    output_id=output_id,
                    matrix_id=matrix_id_recent,
                    last_read=current_time() - timedelta(days=1),
                )
            )
            db.session.commit()

            views_before = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_before) == 2

        result = clean_variable_views(dry_run=False, retention_time=7)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1

        with db():
            views_after = db.session.query(OutputVariablesViewsModel).all()
            assert len(views_after) == 1
            assert views_after[0].matrix_id == matrix_id_recent
