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
        local_nb_cores = LocalConfig.from_dict({"enable_nb_cores_detection": True}).nb_cores
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
            "/v1/launcher/nbcores?launcher=local",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()
        assert actual == nb_cores_expected

        # Check that the endpoint raise an exception when the "slurm" launcher is requested.
        res = client.get(
            "/v1/launcher/nbcores?launcher=slurm",
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
            "/v1/launcher/nbcores?launcher=unknown",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        actual = res.json()
        assert actual == {
            "description": "Unknown solver configuration: 'unknown'",
            "exception": "UnknownSolverConfig",
        }

    def test_get_launcher_time_limit(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        res = client.get(
            "/v1/launcher/time-limit",
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
            "/v1/launcher/time-limit?launcher=local",
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
        assert actual == {
            "description": "Unknown solver configuration: 'unknown'",
            "exception": "UnknownSolverConfig",
        }
