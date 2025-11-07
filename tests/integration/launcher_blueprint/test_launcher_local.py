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

from starlette.testclient import TestClient

from antarest.core.config import LocalConfig


# noinspection SpellCheckingInspection
class TestLauncherConfiguration:
    """
    The purpose of this unit test is to check the `/v1/launcher/launchers` endpoint.
    """

    def test_get_launchers(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        # NOTE: we have `enable_nb_cores_detection: True` in `tests/integration/assets/config.template.yml`.
        local_config = LocalConfig.from_dict(
            {"id": "local_id", "type": "local", "name": "local", "enable_nb_cores_detection": True}
        )
        expected_launchers = [
            {
                "id": "local_id",
                "name": "local",
                "nbCores": {
                    "min": local_config.nb_cores.min,
                    "max": local_config.nb_cores.max,
                    "default": local_config.nb_cores.default,
                },
                "timeLimit": {
                    "min": local_config.time_limit.min,
                    "max": local_config.time_limit.max,
                    "default": local_config.time_limit.default,
                },
                "versions": ["7.0", "8.8"],
            }
        ]

        res = client.get(
            "/v1/launcher/launchers",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual["launchers"] == expected_launchers
        assert actual["defaultLauncher"] == "local_id"

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
        res = client.post(f"/v1/launcher/run/{study_id}", headers={"Authorization": f"Bearer {admin_access_token}"})
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
