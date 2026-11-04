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
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.tasks.model import TaskResult
from antarest.core.utils.utils import current_time
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from tests.helpers import create_raw_study, create_variant_study, with_db_context


@with_db_context
def test_output_archival_includes_variants_but_excludes_external_and_archived_studies(tmp_path: Path) -> None:
    now = current_time()
    repository = StudyMetadataRepository()
    repository.session.add_all(
        [
            create_raw_study(id="external", workspace="external", updated_at=now),
            create_raw_study(id="archived", workspace=DEFAULT_WORKSPACE_NAME, archived=True, updated_at=now),
            create_variant_study(id="variant", updated_at=now),
        ]
    )
    repository.session.commit()
    study_service, output_service = Mock(repository=repository), Mock()
    output_service.get_outputs_to_archive.return_value = ["output"]

    result = archive_old_studies(study_service, output_service, 60, 7, True, tmp_path)

    assert result.status == BackGroundTaskStatus.SUCCESS
    assert result.archived_outputs == 1
    assert result.archived_studies == 0
    assert output_service.get_outputs_to_archive.call_args.args[0] == "variant"


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("active_study", [False, True])
@with_db_context
def test_archives_study_based_on_its_access_date(tmp_path: Path, dry_run: bool, active_study: bool) -> None:
    now = current_time()
    old = now - datetime.timedelta(days=90)
    repository = StudyMetadataRepository()
    repository.session.add(
        create_raw_study(id="study", workspace=DEFAULT_WORKSPACE_NAME, last_access=now if active_study else old)
    )
    repository.session.commit()
    study_service, output_service = Mock(repository=repository), Mock()
    output_service.get_outputs_to_archive.return_value = ["old"]
    study_service.task_service.status_task.return_value.result = TaskResult(success=True, message="ok")

    result = archive_old_studies(study_service, output_service, 60, 7, dry_run, tmp_path)

    assert result.status == BackGroundTaskStatus.SUCCESS
    assert result.archived_studies == int(not active_study)
    assert result.archived_outputs == int(active_study)
    if not active_study:
        output_service.get_outputs_to_archive.assert_not_called()
    if dry_run:
        study_service.archive.assert_not_called()
        output_service.archive_output.assert_not_called()
    elif active_study:
        study_service.archive.assert_not_called()
        output_service.archive_output.assert_called_once()
        assert output_service.archive_output.call_args.args == ("study", "old")
    else:
        study_service.archive.assert_called_once()
        output_service.archive_output.assert_not_called()
