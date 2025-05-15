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

import http

import pytest
from starlette.testclient import TestClient

from antarest.core.config import LocalConfig, TimeLimitConfig


# noinspection SpellCheckingInspection
@pytest.mark.integration_test
class TestLauncherNbCores:
    """
    The purpose of this unit test is to check the `/v1/launcher/nbcores` endpoint.
    """

    def test_get_launcher_nb_cores(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        # NOTE: we have `enable_nb_cores_detection: True` in `tests/integration/assets/config.template.yml`.
        local_nb_cores = LocalConfig.from_dict(
            {"id": "id", "type": "local", "name": "name", "enable_nb_cores_detection": True}
        ).nb_cores
        nb_cores_expected = local_nb_cores.to_json()
        res = client.get(
            "/v1/launcher/nbcores",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == nb_cores_expected

        res = client.get(
            "/v1/launcher/nbcores?launcher=default",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == nb_cores_expected

        res = client.get(
            "/v1/launcher/nbcores?launcher=local_id",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == nb_cores_expected

        # Check that the endpoint raise an exception when the "slurm" launcher is requested.
        res = client.get(
            "/v1/launcher/nbcores?launcher=slurm_id",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        actual = res.json()
        assert actual == {
            "description": "Unknown solver configuration: 'slurm_id'",
            "exception": "UnknownSolverConfig",
        }

        # Check that the endpoint raise an exception when an unknown launcher is requested.
        res = client.get(
            "/v1/launcher/nbcores?launcher=unknown",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        actual = res.json()
        assert actual["description"] == "Unknown solver configuration: 'unknown'"
        assert actual["exception"] == "UnknownSolverConfig"

    def test_get_launcher_time_limit(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        res = client.get(
            "/v1/launcher/time-limit?launcher=local_id",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        expected = TimeLimitConfig().to_json()
        assert actual == expected

        res = client.get(
            "/v1/launcher/time-limit?launcher=default",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == expected

        res = client.get(
            "/v1/launcher/time-limit?launcher=local_id",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == expected

        # Check that the endpoint raise an exception when the "slurm" launcher is requested.
        res = client.get(
            "/v1/launcher/time-limit?launcher=slurm",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        actual = res.json()
        assert actual == {
            "description": "Unknown solver configuration: 'slurm'",
            "exception": "UnknownSolverConfig",
        }

        # Check that the endpoint raise an exception when an unknown launcher is requested.
        res = client.get(
            "/v1/launcher/time-limit?launcher=unknown",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        actual = res.json()
        assert actual["description"] == "Unknown solver configuration: 'unknown'"
        assert actual["exception"] == "UnknownSolverConfig"

    def test_jobs_permissions(
        self,
        client: TestClient,
        user_access_token: str,
        admin_access_token: str,
    ) -> None:
        # create an admin study with no permissions
        res = client.post(
            "/v1/studies",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "study_admin"},
        )
        res.raise_for_status()
        # get the study_id
        study_id = res.json()

        # launch a job with the admin user
        res = client.post(
            f"/v1/launcher/run/{study_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"launcher": "local"},
        )
        res.raise_for_status()
        job_id = res.json()["job_id"]

        # check that the user cannot see the job
        res = client.get(
            "/v1/launcher/jobs",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert job_id not in [job.get("id") for job in res.json()]

        # check that the admin can see the job
        res = client.get(
            "/v1/launcher/jobs",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        res.raise_for_status()
        assert job_id in [job.get("id") for job in res.json()]
