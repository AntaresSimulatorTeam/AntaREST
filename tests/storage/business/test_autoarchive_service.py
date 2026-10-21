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

import datetime
import tempfile
from pathlib import Path
from unittest.mock import ANY, Mock, call

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.model import TaskResult
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.output.repository import OutputRepository
from antarest.output.service import OutputService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from tests.helpers import create_raw_study, create_variant_study, with_db_context


@with_db_context
def test_auto_archival() -> None:
    mock_study_service = Mock(spec=StudyService)
    mock_output_service = Mock(spec=OutputService)

    now = current_time()

    repository = StudyMetadataRepository()

    # Add some studies in the database
    db_session = repository.session
    db_session.add_all(
        [
            ConfigData(
                owner=DEFAULT_ADMIN_USER.id,
                key=ConfigDataAppKeys.OUTPUT_ARCHIVING_REFERENCE_DATE,
                value=now.isoformat(),
            ),
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

    outputs = OutputRepository()
    for study_id, last_access in [
        ("a", now - datetime.timedelta(days=61)),
        ("b", now - datetime.timedelta(days=61)),
        ("e", now - datetime.timedelta(days=61)),
        ("d", now),
    ]:
        outputs.initialize(study_id, "output", last_access, False)

    def archive_output(study_id: str, output_id: str, *, last_access_before: datetime.datetime) -> str:
        outputs.update_archived(study_id, output_id, True)
        return f"archive-{study_id}"

    mock_study_service.repository = repository
    mock_study_service.storage_service = Mock()
    mock_study_service.storage_service.variant_study_service = Mock()
    mock_study_service.storage_service.variant_study_service.clear_all_snapshots.return_value = 0
    mock_study_service.task_service = Mock()
    mock_study_service.task_service.status_task.return_value.result = TaskResult(success=True, message="ok")
    mock_study_service.get_study = repository.get
    mock_output_service.archive_output.side_effect = archive_output
    mock_output_service.has_outputs_to_preserve.side_effect = outputs.has_outputs_to_preserve

    result = archive_old_studies(
        study_service=mock_study_service,
        output_service=mock_output_service,
        threshold_days=60,
        snapshot_retention_days=7,
        dry_run=False,
        lock_folder=Path(tempfile.gettempdir()),
    )

    assert result.status == BackGroundTaskStatus.SUCCESS
    mock_output_service.initialize_outputs_metadata.assert_any_call("d", now)
    assert result.archived_outputs == 2
    mock_study_service.archive.assert_not_called()
    mock_output_service.archive_output.assert_has_calls(
        [call("b", "output", last_access_before=ANY), call("e", "output", last_access_before=ANY)], any_order=True
    )
    mock_study_service.storage_service.variant_study_service.clear_all_snapshots.assert_called_once_with(
        datetime.timedelta(days=7)
    )
