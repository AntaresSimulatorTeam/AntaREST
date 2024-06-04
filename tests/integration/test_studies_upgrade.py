import os

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion

RUN_ON_WINDOWS = os.name == "nt"


class TestStudyUpgrade:
    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    def test_upgrade_study__next_version(self, client: TestClient, user_access_token: str, study_id: str):
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert "710" in task.result.message, f"Version not in {task.result.message=}"

    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    def test_upgrade_study__target_version(self, client: TestClient, user_access_token: str, study_id: str):
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
        assert target_version in task.result.message, f"Version not in {task.result.message=}"

    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    def test_upgrade_study__bad_target_version(self, client: TestClient, user_access_token: str, study_id: str):
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
        assert target_version in task.result.message, f"Version not in {task.result.message=}"

    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    def test_upgrade_study__unmet_requirements(self, client: TestClient, admin_access_token: str):
        """
        Test that an upgrade with unmet requirements fails, corresponding to the two following cases:
            - the study is a raw study with at least one child study
            - the study is a variant study

        Args:
            client:
            admin_access_token

        Returns:
        """

        # create a raw study
        res = client.post(
            "/v1/studies",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "test_upgrade_study__unmet_requirements__raw_study"},
        )
        assert res.status_code == 201
        uuid = res.json()

        # create a child variant study
        res = client.post(
            f"/v1/studies/{uuid}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "test_upgrade_study__unmet_requirements__variant_study"},
        )
        assert res.status_code == 200
        child_uuid = res.json()

        # upgrade the raw study
        res = client.put(
            f"/v1/studies/{uuid}/upgrade",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        # check that the upgrade failed (HttpException:417, with the expected message)
        assert res.status_code == 417
        assert res.json() == {
            "description": f"Raw Study {uuid} cannot be upgraded: it has children studies",
            "exception": "StudyUpgradeRequirementsNotMet",
        }

        # upgrade the variant study
        res = client.put(
            f"/v1/studies/{child_uuid}/upgrade",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        # check that the upgrade failed (HttpException:417, with the expected message)
        assert res.status_code == 417
        assert res.json() == {
            "description": f"Variant study {child_uuid} cannot be upgraded",
            "exception": "StudyUpgradeRequirementsNotMet",
        }
