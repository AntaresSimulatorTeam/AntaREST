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
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study, StudyRepairReport
from tests.integration.utils import wait_task_completion


class TestRepairStudy:
    def test_repair_archive_consistency_endpoint(
        self,
        client: TestClient,
        admin_access_token: str,
        tmp_path: Path,
    ) -> None:
        admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post(
            "/v1/studies",
            headers=admin_headers,
            params={"name": "repairable-study"},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        res = client.put(f"/v1/studies/{study_id}/archive", headers=admin_headers)
        assert res.status_code == 200, res.json()
        archive_task = wait_task_completion(client, admin_access_token, res.json())
        assert archive_task.status == TaskStatus.COMPLETED, archive_task
        assert archive_task.result is not None and archive_task.result.success

        archive_path = tmp_path / "archive_dir" / f"{study_id}.7z"
        study_path = tmp_path / "internal_workspace" / study_id
        assert archive_path.exists()
        assert not study_path.exists()

        with db():
            study = db.session.get(Study, study_id)
            assert study is not None
            study.archived = False
            db.session.commit()

        res = client.get(f"/v1/studies/{study_id}", headers=admin_headers)
        assert res.status_code == 200, res.json()
        assert not res.json()["archived"]

        res = client.post(
            f"/v1/studies/{study_id}/repair",
            headers=admin_headers,
            json={"repairs": ["archive_consistency"], "dry_run": True},
        )
        assert res.status_code == 200, res.json()
        dry_run_task = wait_task_completion(client, admin_access_token, res.json())
        assert dry_run_task.status == TaskStatus.COMPLETED, dry_run_task
        assert dry_run_task.result is not None
        dry_run_report = StudyRepairReport.model_validate_json(dry_run_task.result.return_value)
        assert dry_run_report.dry_run
        assert [issue.code for issue in dry_run_report.issues] == ["archive_consistency_db_fs_mismatch"]
        assert [action.code for action in dry_run_report.proposed_actions] == ["set_archived_true"]
        assert dry_run_report.applied_actions == []

        res = client.get(f"/v1/studies/{study_id}", headers=admin_headers)
        assert res.status_code == 200, res.json()
        assert not res.json()["archived"]

        res = client.post(
            f"/v1/studies/{study_id}/repair",
            headers=admin_headers,
            json={"repairs": ["archive_consistency"], "dry_run": False},
        )
        assert res.status_code == 200, res.json()
        repair_task = wait_task_completion(client, admin_access_token, res.json())
        assert repair_task.status == TaskStatus.COMPLETED, repair_task
        assert repair_task.result is not None and repair_task.result.success
        repair_report = StudyRepairReport.model_validate_json(repair_task.result.return_value)
        assert not repair_report.dry_run
        assert [action.code for action in repair_report.applied_actions] == ["set_archived_true"]

        res = client.get(f"/v1/studies/{study_id}", headers=admin_headers)
        assert res.status_code == 200, res.json()
        assert res.json()["archived"]
