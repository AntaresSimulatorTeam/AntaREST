from starlette.testclient import TestClient


class TestDiskUsage:
    def test_disk_usage_endpoint(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        Verify the functionality of the disk usage endpoint:

        - Ensure a successful response is received.
        - Confirm that the JSON response is an integer which represent a (big enough) directory size.
        """
        res = client.get(
            f"/v1/studies/{study_id}/disk-usage",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        disk_usage = res.json()  # currently: 7.47 Mio on Ubuntu
        assert 7 * 1024 * 1024 < disk_usage < 8 * 1024 * 1024
