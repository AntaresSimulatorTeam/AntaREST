import os

import pytest
from antarest.core.tasks.model import TaskStatus
from starlette.testclient import TestClient
from tests.integration.utils import wait_task_completion

RUN_ON_WINDOWS = os.name == "nt"


class TestStudyUpgrade:
    @pytest.mark.skipif(
        RUN_ON_WINDOWS, reason="This test runs randomly on Windows"
    )
    def test_upgrade_study__next_version(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert (
            "710" in task.result.message
        ), f"Version not in {task.result.message=}"

    @pytest.mark.skipif(
        RUN_ON_WINDOWS, reason="This test runs randomly on Windows"
    )
    def test_upgrade_study__target_version(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        target_version = "720"
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": target_version},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert (
            target_version in task.result.message
        ), f"Version not in {task.result.message=}"

    @pytest.mark.skipif(
        RUN_ON_WINDOWS, reason="This test runs randomly on Windows"
    )
    def test_upgrade_study__bad_target_version(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        target_version = "999"
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": target_version},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.FAILED
        assert (
            target_version in task.result.message
        ), f"Version not in {task.result.message=}"
