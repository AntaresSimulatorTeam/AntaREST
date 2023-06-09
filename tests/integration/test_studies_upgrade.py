import os
import time

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus

RUN_ON_WINDOWS = os.name == "nt"


def wait_task_completion(
    client: TestClient,
    access_token: str,
    task_id: str,
    *,
    timeout: float = 10,
) -> TaskDTO:
    end_time = time.time() + timeout
    while time.time() < end_time:
        time.sleep(0.1)
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
