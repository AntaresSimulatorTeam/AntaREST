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
import json
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from tests.integration.utils import wait_task_completion


class TestRepairStudy:
    def test_repair_study_forbidden(
        self,
        client: TestClient,
        user_access_token: str,
        admin_client: TestClient,
        admin_access_token: str,
    ) -> None:
        res = admin_client.post("/v1/studies", params={"name": "study-for-auth-test"})
        assert res.status_code == 201, res.json()
        study_id = res.json()

        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # Non-admin user gets 403
        res = client.post(f"/v1/studies/{study_id}/_repair", headers=user_headers, json={})
        assert res.status_code == 403

    def test_repair_archive_consistency_endpoint(
        self,
        admin_client: TestClient,
        admin_access_token: str,
        tmp_path: Path,
    ) -> None:
        res = admin_client.post(
            "/v1/studies",
            params={"name": "repairable-study"},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        res = admin_client.put(f"/v1/studies/{study_id}/archive")
        assert res.status_code == 200, res.json()
        archive_task = wait_task_completion(admin_client, admin_access_token, res.json())
        assert archive_task.status == TaskStatus.COMPLETED, archive_task
        assert archive_task.result is not None and archive_task.result.success

        archive_path = tmp_path / "archive_dir" / f"{study_id}.zip"
        study_path = tmp_path / "internal_workspace" / study_id
        assert archive_path.exists()
        assert not study_path.exists()

        with db():
            study = db.session.get(Study, study_id)
            assert study is not None
            study.archived = False
            db.session.commit()

        res = admin_client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200, res.json()
        assert not res.json()["archived"]

        res = admin_client.post(
            f"/v1/studies/{study_id}/_repair",
            json={"repairs": ["archive_consistency"], "dry_run": True},
        )
        assert res.status_code == 200, res.json()
        dry_run_task = wait_task_completion(admin_client, admin_access_token, res.json())
        assert dry_run_task.status == TaskStatus.COMPLETED, dry_run_task
        assert dry_run_task.result is not None
        assert json.loads(dry_run_task.result.return_value) == {
            "study_id": study_id,
            "dry_run": True,
            "issues": [
                {
                    "code": "archive_consistency_db_fs_mismatch",
                    "severity": "error",
                    "message": "Database says the study is unarchived but only the archive exists on disk",
                    "details": {},
                }
            ],
            "proposed_actions": [
                {
                    "code": "set_archived_true",
                    "description": "Mark the study as archived in database",
                    "details": {"archived": True},
                }
            ],
            "applied_actions": [],
            "warnings": [],
        }

        res = admin_client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200, res.json()
        assert not res.json()["archived"]

        res = admin_client.post(
            f"/v1/studies/{study_id}/_repair",
            json={"repairs": ["archive_consistency"], "dry_run": False},
        )
        assert res.status_code == 200, res.json()
        repair_task = wait_task_completion(admin_client, admin_access_token, res.json())
        assert repair_task.status == TaskStatus.COMPLETED, repair_task
        assert repair_task.result is not None and repair_task.result.success
        assert json.loads(repair_task.result.return_value) == {
            "study_id": study_id,
            "dry_run": False,
            "issues": [
                {
                    "code": "archive_consistency_db_fs_mismatch",
                    "severity": "error",
                    "message": "Database says the study is unarchived but only the archive exists on disk",
                    "details": {},
                }
            ],
            "proposed_actions": [
                {
                    "code": "set_archived_true",
                    "description": "Mark the study as archived in database",
                    "details": {"archived": True},
                }
            ],
            "applied_actions": [
                {
                    "code": "set_archived_true",
                    "description": "Mark the study as archived in database",
                    "details": {"archived": True},
                }
            ],
            "warnings": [],
        }

        res = admin_client.get(f"/v1/studies/{study_id}")
        assert res.status_code == 200, res.json()
        assert res.json()["archived"]
