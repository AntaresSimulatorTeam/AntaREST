import time

import pytest
from antarest.core.tasks.model import TaskDTO, TaskStatus
from fastapi import FastAPI
from starlette.testclient import TestClient


def wait_task_completion(
    client: TestClient,
    access_token: str,
    task_id: str,
    *,
    timeout: float = 1,
) -> TaskDTO:
    end_time = time.time() + timeout
    while time.time() < end_time:
        time.sleep(0.01)
        res = client.get(
            f"/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"wait_for_completion": True},
        )
        assert res.status_code == 200
        task = TaskDTO(**res.json())
        if task.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            return task
    raise TimeoutError(f"{timeout} seconds")


class TestStudyUpgrade:
    @pytest.fixture(name="client")
    def fixture_client(self, app: FastAPI) -> TestClient:
        """Get the webservice client used for unit testing"""
        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture(name="admin_access_token")
    def fixture_admin_access_token(self, client: TestClient) -> str:
        """Get the admin user access token used for authentication"""
        res = client.post(
            "/v1/login",
            json={"username": "admin", "password": "admin"},
        )
        assert res.status_code == 200
        credentials = res.json()
        return credentials["access_token"]

    @pytest.fixture(name="user_access_token")
    def fixture_user_access_token(
        self,
        client: TestClient,
        admin_access_token: str,
    ) -> str:
        """Get a classic user access token used for authentication"""
        res = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "George", "password": "mypass"},
        )
        assert res.status_code == 200
        res = client.post(
            "/v1/login",
            json={"username": "George", "password": "mypass"},
        )
        assert res.status_code == 200
        credentials = res.json()
        return credentials["access_token"]

    @pytest.fixture(name="study_id")
    def fixture_study_id(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> str:
        """Get the ID of the study to upgrade"""
        res = client.get(
            "/v1/studies",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        study_ids = res.json()
        return next(iter(study_ids))

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
