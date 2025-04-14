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

from typing import Any, Sequence
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient


@pytest.mark.integration_test
class TestSolverVersions:
    """
    The purpose of this unit test is to check the `/v1/launcher/versions` endpoint.
    """

    def test_get_solver_versions(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        # Fetch the default server version from the configuration file.
        # NOTE: the value is defined in `tests/integration/assets/config.template.yml`.
        res = client.get(
            "/v1/launcher/versions",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == ["700"]

        res = client.get(
            "/v1/launcher/versions?solver=default",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == ["700"]

        res = client.get(
            "/v1/launcher/versions?solver=local_id",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == ["700"]

        res = client.get(
            "/v1/launcher/versions?solver=slurm",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == []

    def test_get_solver_versions__default(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        """
        This unit test checks that the default value
        of the `solver` parameter is indeed "default".
        """

        def get_versions(_: Any, solver: str) -> Sequence[str]:
            # To distinguish between the default value and the local value,
            # we use a different value for each `solver` value.
            versions = {"default": ["123"], "local": ["456"], "slurm": ["798"]}
            return versions[solver]

        with patch(
            "antarest.launcher.service.LauncherService.get_solver_versions",
            new=get_versions,
        ):
            res = client.get(
                "/v1/launcher/versions",
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
        res.raise_for_status()
        actual = res.json()
        assert actual == ["123"]
