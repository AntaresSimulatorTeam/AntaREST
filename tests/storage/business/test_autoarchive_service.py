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

import datetime
from unittest.mock import Mock

from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import TaskStatus
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.output.output_service import OutputService
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from tests.helpers import create_raw_study, create_variant_study, with_db_context


@with_db_context
def test_auto_archival() -> None:
    """Test that archive_old_studies correctly identifies and archives old studies."""
    mock_study_service = Mock(spec=StudyService)
    mock_output_service = Mock(spec=OutputService)

    now = current_time()

    repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))

    # Add some studies in the database
    db_session = repository.session
    db_session.add_all(
        [
            create_raw_study(
                id="a",
                workspace="not default",
                updated_at=now - datetime.timedelta(days=61),
            ),
            create_raw_study(
                id="b",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=59),
            ),
            create_raw_study(
                id="c",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=61),
                archived=True,
            ),
            create_raw_study(
                id="d",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=61),
                archived=False,
            ),
            create_variant_study(
                id="e",
                updated_at=now - datetime.timedelta(days=61),
            ),
            create_variant_study(
                id="f",
                updated_at=now - datetime.timedelta(days=1),
            ),
        ]
    )
    db_session.commit()

    mock_study_service.repository = repository
    mock_study_service.storage_service = Mock()
    mock_study_service.storage_service.variant_study_service = Mock()
    mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0
    mock_study_service.task_service = Mock()
    mock_study_service.archive.side_effect = TaskAlreadyRunning
    mock_study_service.get_study = repository.get
    mock_output_service.archive_outputs.return_value = ["task1"]

    result = archive_old_studies(
        study_service=mock_study_service,
        output_service=mock_output_service,
        threshold_days=60,
        snapshot_retention_days=7,
        dry_run=False,
    )

    # The task should complete successfully (TaskAlreadyRunning is handled gracefully)
    assert result.status == TaskStatus.SUCCESS

    # Check that the raw study "d" was about to be archived but failed because the task was already running
    mock_study_service.archive.assert_called_once_with("d")

    # Check that the variant outputs are deleted for the variant study "e"
    mock_output_service.archive_outputs.assert_called_once_with("e")

    # Check if the `clear_all_snapshots` method was called with default values
    mock_study_service.storage_service.variant_study_service.clear_all_snapshots.assert_called_once_with(
        datetime.timedelta(days=7)
    )
