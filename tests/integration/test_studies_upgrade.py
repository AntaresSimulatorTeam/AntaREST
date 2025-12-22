# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import sys

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion

RUN_ON_WINDOWS = sys.platform == "win32"


class TestStudyUpgrade:
    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    def test_upgrade_study__next_version(
        self, client: TestClient, user_access_token: str, internal_study_id: str
    ) -> None:
        res = client.put(
            f"/v1/studies/{internal_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result.message == f"Successfully upgraded study '{internal_study_id}' to version 7.1"

    @pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
    @pytest.mark.parametrize("target_version", ["720", "7.2"])
    def test_upgrade_study__target_version(
        self, client: TestClient, user_access_token: str, internal_study_id: str, target_version: str
    ) -> None:
        res = client.put(
            f"/v1/studies/{internal_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": target_version},
        )
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result.message == f"Successfully upgraded study '{internal_study_id}' to version 7.2"

    def test_upgrade_study__bad_target_version(
        self, client: TestClient, user_access_token: str, internal_study_id: str
    ) -> None:
        target_version = "999"
        res = client.put(
            f"/v1/studies/{internal_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": target_version},
        )
        assert res.status_code == 400
        assert res.json()["exception"] == "UnsupportedStudyVersion"
        assert "Version '9.9' isn't among supported versions" in res.json()["description"]

    def test_upgrade_study__unmet_requirements(self, client: TestClient, admin_access_token: str) -> None:
        """
        Test that an upgrade with unmet requirements fails, corresponding to the two following cases:
            - the study is a raw study with at least one child study
            - the study is a variant study
        """

        # set the admin access token in the client headers
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        # create a raw study
        res = client.post("/v1/studies", params={"name": "My Study"})
        assert res.status_code == 201, res.json()
        uuid = res.json()

        # create a child variant study
        res = client.post(f"/v1/studies/{uuid}/variants", params={"name": "foo"})
        assert res.status_code == 200, res.json()
        child_uuid = res.json()

        # upgrade the raw study
        res = client.put(f"/v1/studies/{uuid}/upgrade")

        # check that the upgrade failed (HttpException:417, with the expected message)
        assert res.status_code == 417, res.json()
        assert res.json() == {
            "description": "Upgrade not supported for parent of variants",
            "exception": "StudyVariantUpgradeError",
        }

        # upgrade the variant study
        res = client.put(f"/v1/studies/{child_uuid}/upgrade")

        # check that the upgrade failed (HttpException:417, with the expected message)
        assert res.status_code == 417, res.json()
        assert res.json() == {
            "description": "Upgrade not supported for variant study",
            "exception": "StudyVariantUpgradeError",
        }
