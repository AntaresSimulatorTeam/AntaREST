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

"""The disk space analysis of a study must be invalidated by operations changing its size without editing it."""

import io
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.study.model import StudyDiskSpaceAnalysis
from antarest.study.repository import StudyDiskSpaceRepository
from tests.integration.utils import wait_task_completion


def _add_disk_space_analysis(study_id: str) -> None:
    with db():
        StudyDiskSpaceRepository().save(
            StudyDiskSpaceAnalysis(study_id=study_id, disk_space_bytes=1, last_analysis_date=current_time())
        )


def _has_disk_space_analysis(study_id: str) -> bool:
    with db():
        return StudyDiskSpaceRepository().get(study_id) is not None


def _managed_study_with_output(client: TestClient, internal_study_id: str) -> tuple[str, str]:
    """Copies the internal study with its outputs, as outputs of external studies are unarchived by a remote worker."""
    res = client.post(
        f"/v1/studies/{internal_study_id}/copy",
        params={"study_name": "copied_study", "with_outputs": True, "use_task": False},
    )
    assert res.status_code == 201, res.json()
    study_id = res.json()
    outputs = client.get(f"/v1/studies/{study_id}/outputs").json()
    return study_id, next(output["id"] for output in outputs if not output["archived"])


def test_output_archive_and_unarchive_invalidate_analysis(admin_client: TestClient, internal_study_id: str) -> None:
    study_id, output_id = _managed_study_with_output(admin_client, internal_study_id)

    _add_disk_space_analysis(study_id)
    task_id = admin_client.post(f"/v1/studies/{study_id}/outputs/{output_id}/_archive").json()
    assert wait_task_completion(admin_client, None, task_id).status == TaskStatus.COMPLETED
    assert not _has_disk_space_analysis(study_id)

    _add_disk_space_analysis(study_id)
    task_id = admin_client.post(f"/v1/studies/{study_id}/outputs/{output_id}/_unarchive").json()
    assert wait_task_completion(admin_client, None, task_id).status == TaskStatus.COMPLETED
    assert not _has_disk_space_analysis(study_id)


def test_output_deletion_invalidates_analysis(admin_client: TestClient, internal_study_id: str) -> None:
    study_id, output_id = _managed_study_with_output(admin_client, internal_study_id)

    _add_disk_space_analysis(study_id)
    res = admin_client.delete(f"/v1/studies/{study_id}/outputs/{output_id}")
    assert res.status_code == 200, res.json()
    assert not _has_disk_space_analysis(study_id)


def test_output_import_invalidates_analysis(admin_client: TestClient, output_zip: Path) -> None:
    study_id = admin_client.post("/v1/studies", params={"name": "foo"}).json()

    _add_disk_space_analysis(study_id)
    res = admin_client.post(f"/v1/studies/{study_id}/output", files={"output": io.BytesIO(output_zip.read_bytes())})
    assert res.status_code == 202, res.json()
    assert not _has_disk_space_analysis(study_id)


def test_study_archive_and_unarchive_invalidate_analysis(admin_client: TestClient) -> None:
    study_id = admin_client.post("/v1/studies", params={"name": "foo"}).json()

    _add_disk_space_analysis(study_id)
    task_id = admin_client.put(f"/v1/studies/{study_id}/archive").json()
    assert wait_task_completion(admin_client, None, task_id).status == TaskStatus.COMPLETED
    assert not _has_disk_space_analysis(study_id)

    _add_disk_space_analysis(study_id)
    task_id = admin_client.put(f"/v1/studies/{study_id}/unarchive").json()
    assert wait_task_completion(admin_client, None, task_id).status == TaskStatus.COMPLETED
    assert not _has_disk_space_analysis(study_id)
