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

"""Integration tests for the auto-archive task."""

import datetime
from unittest.mock import Mock

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.output_service import OutputService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from tests.helpers import create_raw_study, create_variant_study


class TestArchiveOldStudiesIntegration:
    def test_archives_old_studies_dry_run(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create old studies that should be archived
            db_session.add_all(
                [
                    create_raw_study(
                        id="old_raw",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=90),
                        archived=False,
                    ),
                    create_variant_study(
                        id="old_variant",
                        updated_at=now - datetime.timedelta(days=90),
                    ),
                    create_raw_study(
                        id="recent_raw",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=30),
                        archived=False,
                    ),
                ]
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=True,
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.dry_run is True
        # In dry_run, we still count what would be archived (old_raw + old_variant)
        assert result.archived_studies == 2

        # But no actual archive calls should be made
        mock_study_service.archive.assert_not_called()
        mock_output_service.archive_outputs.assert_not_called()

    def test_returns_success_with_no_old_studies(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create only recent studies
            db_session.add_all(
                [
                    create_raw_study(
                        id="recent1",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=30),
                        archived=False,
                    ),
                    create_raw_study(
                        id="recent2",
                        workspace=DEFAULT_WORKSPACE_NAME,
                        updated_at=now - datetime.timedelta(days=10),
                        archived=False,
                    ),
                ]
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = "snapshot_task"
            mock_study_service.task_service = Mock()

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=False,
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.archived_studies == 0
        mock_study_service.task_service.await_task.assert_called_once_with("snapshot_task")
        assert result.duration_seconds >= 0

    def test_excludes_already_archived_studies(self, db_middleware):
        mock_study_service = Mock(spec=StudyService)
        mock_output_service = Mock(spec=OutputService)

        now = current_time()

        with db():
            repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))
            db_session = repository.session

            # Create an old but already archived study
            db_session.add(
                create_raw_study(
                    id="already_archived",
                    workspace=DEFAULT_WORKSPACE_NAME,
                    updated_at=now - datetime.timedelta(days=90),
                    archived=True,
                ),
            )
            db_session.commit()

            mock_study_service.repository = repository
            mock_study_service.storage_service = Mock()
            mock_study_service.storage_service.variant_study_service = Mock()
            mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0

        result = archive_old_studies(
            study_service=mock_study_service,
            output_service=mock_output_service,
            threshold_days=60,
            snapshot_retention_days=7,
            dry_run=True,
        )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.archived_studies == 0
