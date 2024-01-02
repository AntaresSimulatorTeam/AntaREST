from starlette.testclient import TestClient


class TestDiskUsage:
    def test_disk_usage_endpoint(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        we verify the endpoint work:
        - we get a response
        - the length of the response json is big enough
        """
        res = client.get(
            f"/v1/studies/{study_id}/disk-usage",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual > 1000
