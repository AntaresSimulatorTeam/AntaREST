import numpy as np
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


class TestGenerateThermalClusterTimeseries:
    def test_lifecycle_nominal(self, client: TestClient, user_access_token: str) -> None:
        # Study preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        # Create 1 cluster in area1
        cluster_1 = "Cluster 1"
        nominal_capacity_cluster_1 = 1000.0
        preparer.create_thermal(
            study_id, area1_id, name=cluster_1, group="Lignite", nominalCapacity=nominal_capacity_cluster_1
        )

        # Create 2 clusters in area1
        cluster_2 = "Cluster 2"
        cluster_3 = "Cluster 3"
        nominal_capacity_cluster_2 = 40.0
        preparer.create_thermal(
            study_id, area2_id, name=cluster_2, group="Nuclear", nominalCapacity=nominal_capacity_cluster_2
        )
        preparer.create_thermal(study_id, area2_id, name=cluster_3, group="Gas", genTs="force no generation")

        # Update modulation for Cluster 2.
        matrix = np.zeros(shape=(8760, 4)).tolist()
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/prepro/{area2_id}/{cluster_2.lower()}/modulation"},
            json=matrix,
        )
        assert res.status_code == 204

        # Timeseries generation should succeed
        nb_years = 3
        res = client.put(f"/v1/studies/{study_id}/timeseries/generate", params={"nb_years": nb_years})
        assert res.status_code in {200, 201}

        # Check matrices
        # First one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area1_id}/{cluster_1.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data[1] == nb_years * [nominal_capacity_cluster_1]
        # Second one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area2_id}/{cluster_2.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data[1] == nb_years * [0]  # should be zeros as the modulation matrix is only zeros
        # Third one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area2_id}/{cluster_3.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data == [[]]  # no generation c.f. gen-ts parameter

    def test_errors(self, client: TestClient, user_access_token: str) -> None:
        # Study Preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]

        # Create a cluster without nominal power
        cluster_name = "Cluster 1"
        preparer.create_thermal(study_id, area1_id, name=cluster_name, group="Lignite")
        # Timeseries generation fails because there's no nominal power
        res = client.put(f"/v1/studies/{study_id}/timeseries/generate")
        assert res.status_code == 500
        assert "Nominal power must be strictly positive, got 0.0" in res.json()["description"]

        # Timeseries generation fails because `nb_years` minimal value is 0.
        res = client.put(f"/v1/studies/{study_id}/timeseries/generate", params={"nb_years": -4})
        assert res.status_code == 422
        assert res.json()["exception"] == "RequestValidationError"
        assert res.json()["description"] == "ensure this value is greater than 0"
