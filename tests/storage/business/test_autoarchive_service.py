# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.cache import ICache
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.helpers import with_db_context


@with_db_context
def test_auto_archival(tmp_path: Path):
    workspace_path = tmp_path / "workspace_test"
    auto_archive_service = AutoArchiveService(
        Mock(spec=StudyService),
        Config(storage=StorageConfig(workspaces={"test": WorkspaceConfig(path=workspace_path)})),
    )

    now = datetime.datetime.now()

    repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))

    # Add some studies in the database
    db_session = repository.session
    db_session.add_all(
        [
            RawStudy(
                id="a",
                workspace="not default",
                updated_at=now - datetime.timedelta(days=61),
            ),
            RawStudy(
                id="b",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=59),
            ),
            RawStudy(
                id="c",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=61),
                archived=True,
            ),
            RawStudy(
                id="d",
                workspace=DEFAULT_WORKSPACE_NAME,
                updated_at=now - datetime.timedelta(days=61),
                archived=False,
            ),
            VariantStudy(
                id="e",
                updated_at=now - datetime.timedelta(days=61),
            ),
        ]
    )
    db_session.commit()

    study_service = auto_archive_service.study_service
    study_service.repository = repository

    study_service.storage_service = Mock()
    study_service.storage_service.variant_study_service = Mock()
    study_service.archive.side_effect = TaskAlreadyRunning
    study_service.get_study = repository.get

    auto_archive_service._try_archive_studies()

    # Check that the raw study "d" was about to be archived but failed because the task was already running
    study_service.archive.assert_called_once_with("d", params=RequestParameters(DEFAULT_ADMIN_USER))

    # Check that the snapshot of the variant study "e" is cleared
    study_service.storage_service.variant_study_service.clear_snapshot.assert_called_once()
    calls = study_service.storage_service.variant_study_service.clear_snapshot.call_args_list
    assert len(calls) == 1
    clear_snapshot_call = calls[0]
    actual_study = clear_snapshot_call[0][0]
    assert actual_study.id == "e"

    # Check that the variant outputs are deleted for the variant study "e"
    study_service.archive_outputs.assert_called_once_with("e", params=RequestParameters(DEFAULT_ADMIN_USER))

    # Check if variant snapshots with date older than variant_snapshot_lifespan_days argument are cleared
