import multiprocessing
import pytest
from starlette.testclient import TestClient


@pytest.mark.integration_test
class TestlauncherNbcores:
    """
    The purpose of this unit test is to check the `/v1/launcher/nbcores` endpoint.
    """

    def test_get_launcher_nbcore(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        # Test The endpoint /v1/launcher/nbcores
        # Fetch the default server version from the configuration file.
        # NOTE: the value is defined in `tests/integration/assets/config.template.yml`.
        max_cpu = multiprocessing.cpu_count()
        default = max(1, max_cpu - 2)
        nb_cores_expected = {"defaultValue": default, "max": max_cpu, "min": 1}
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
