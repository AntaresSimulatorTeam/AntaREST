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
        user_headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.get(
            f"/v1/studies/{study_id}/disk-usage",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        disk_usage = res.json()  # currently: 7.47 Mio on Ubuntu
        assert 7 * 1024 * 1024 < disk_usage < 8 * 1024 * 1024

        # Study copy
        copied = client.post(
            f"/v1/studies/{study_id}/copy?dest=copied&use_task=false",
            headers=user_headers,
        )
        assert copied.status_code == 201
        parent_id = copied.json()

        # Create variant
        res = client.post(
            f"/v1/studies/{parent_id}/variants",
            headers=user_headers,
            params={"name": "Variant Test"},
        )
        assert res.status_code == 200
        variant_id = res.json()

        res = client.get(
            f"/v1/studies/{variant_id}/disk-usage",
            headers=user_headers,
        )
        assert res.status_code == 200
        assert res.json() == 0
