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
        res = client.get(
            f"/v1/studies/{study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        assert res["version"] == 700

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

        res = client.get(
            f"/v1/studies/{study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        assert res["version"] == 710

    @pytest.mark.skipif(
        RUN_ON_WINDOWS, reason="This test runs randomly on Windows"
    )
    def test_upgrade_study__that_has_children(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        # Copy the study to manage it
        managed_study_id = client.post(
            f"/v1/studies/{study_id}/copy?dest=managed_study&with_outputs=false&use_task=false",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()

        # Creation of 2 variants
        res = client.post(
            f"/v1/studies/{managed_study_id}/variants?name=foo_1",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        variant_id_of_level_1 = res.json()

        res = client.post(
            f"/v1/studies/{variant_id_of_level_1}/variants?name=foo_2",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        variant_id_of_level_2 = res.json()

        # Upgrade parent study
        res = client.put(
            f"/v1/studies/{managed_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        # Asserts that the task is completed
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert (
            "710" in task.result.message
        ), f"Version not in {task.result.message=}"

        # Asserts that the 3 studies (parent and 2 variants) have been upgraded
        res = client.get(
            f"/v1/studies/{managed_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        assert res["version"] == 710
        res = client.get(
            f"/v1/studies/{variant_id_of_level_1}/synthesis",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        print(res)
        assert res["version"] == 710

        res = client.get(
            f"/v1/studies/{variant_id_of_level_1}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        print(res)
        assert res["version"] == 710
        res = client.get(
            f"/v1/studies/{variant_id_of_level_2}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        ).json()
        assert res["version"] == 710

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
