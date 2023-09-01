from urllib.parse import quote

import pytest
from starlette.testclient import TestClient

from antarest.study.business.area_management import AreaType


@pytest.mark.unit_test
class TestEditMatrix:
    """
    Test the end points "/studies/{uuid}/matrix".
    """

    def test_edit_matrix__links_parameters(
        self,
        client: TestClient,
        user_access_token: str,
    ):
        """
        This test creates a new study in the `internal_workspace` directory.
        It adds 2 areas and a link between.
        The link parameters contain a matrix which is updated with `edit_matrix`.
        We check several operations on the matrix.
        """
        res = client.post(
            "/v1/studies?name=foo",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        study_id = res.json()

        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "Zone FR",
                "type": AreaType.AREA.value,
                "metadata": {"country": "FR"},
            },
        )
        res.raise_for_status()
        area1_id: str = res.json()["id"]

        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "Zone DE",
                "type": AreaType.AREA.value,
                "metadata": {"country": "DE"},
            },
        )
        res.raise_for_status()
        area2_id: str = res.json()["id"]

        res = client.post(
            f"/v1/studies/{study_id}/links",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "area1": area1_id,
                "area2": area2_id,
            },
        )
        res.raise_for_status()

        # Link parameters between two areas are stored in only one of the two
        # areas in the "input/links" tree. One area acts as source (`area_from`)
        # and the other as target (`area_to`).
        # Parameters are stored in the target area (`area_to`).
        # The choice as to which area plays the role of source or target is made
        # arbitrarily by sorting the area IDs in lexicographic order.
        # The first will be the source and the second will be the target.
        area_from, area_to = sorted([area1_id, area2_id])
        area_from_q = quote(area_from)  # used in query string
        area_to_q = quote(area_to)  # used in query string

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        initial_data = res.json()["data"]

        # only one cell
        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "slices": [{"row_from": 0, "column_from": 0}],
                    "operation": {
                        "operation": "+",
                        "value": 1,
                    },
                }
            ],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        new_data = res.json()["data"]
        assert new_data != initial_data
        assert new_data[0][0] == 1

        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "slices": [
                        {"row_from": 0, "column_from": 0, "column_to": 6}
                    ],
                    "operation": {
                        "operation": "=",
                        "value": 1,
                    },
                }
            ],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        new_data = res.json()["data"]
        assert new_data != initial_data
        assert new_data[0] == [1] * 6

        # The web application generates a query using a list of Matrix Edit Instructions,
        # each containing different coordinates. The first coordinate represents the row
        # ndex, and the second coordinate represents the column index.
        # In the example bellow, the user selects the rows 4 to 6 inclusive and the column 5.
        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "coordinates": [(4, 5)],
                    "operation": {
                        "operation": "=",
                        "value": 42,
                    },
                },
                {
                    "coordinates": [(5, 5)],
                    "operation": {
                        "operation": "=",
                        "value": 42,
                    },
                },
                {
                    "coordinates": [(6, 5)],
                    "operation": {
                        "operation": "=",
                        "value": 42,
                    },
                },
            ],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        new_data = res.json()["data"]
        assert new_data != initial_data
        assert new_data[4][5] == 42
        assert new_data[5][5] == 42
        assert new_data[6][5] == 42

        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "slices": [
                        {"row_from": 0, "row_to": 8760, "column_from": 0}
                    ],
                    "operation": {
                        "operation": "=",
                        "value": 1,
                    },
                }
            ],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        new_data = res.json()["data"]
        assert new_data != initial_data
        assert [a[0] for a in new_data] == [1] * 8760

        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "slices": [
                        {
                            "row_from": 2,
                            "row_to": 4,
                            "column_from": 2,
                            "column_to": 4,
                        },
                        {
                            "row_from": 9,
                            "row_to": 15,
                            "column_from": 1,
                            "column_to": 3,
                        },
                    ],
                    "operation": {
                        "operation": "=",
                        "value": 42,
                    },
                }
            ],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/links/{area_from_q}/{area_to_q}_parameters",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        new_data = res.json()["data"]
        assert new_data != initial_data
        
        assert [[a[i] for a in new_data[2:4]] for i in range(2, 4)] == [[42] * 2] * 2
        assert [[a[i] for a in new_data[9:15]] for i in range(1, 3)] == [[42] * 6] * 2
        

    def test_edit_matrix__thermal_cluster(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        # Given the following Area
        area_id = "fr"

        # Create a cluster
        cluster_id = "cluster 1"
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {
                    "action": "create_cluster",
                    "args": {
                        "area_id": area_id,
                        "cluster_name": cluster_id,
                        "parameters": {},
                    },
                }
            ],
        )
        res.raise_for_status()

        # Even if the matrix is missing, it is now possible to update it
        # because an empty matrix of the right shape is generated automatically.
        obj = [
            {
                "coordinates": [[1, 0]],
                "operation": {"operation": "=", "value": 128},
            }
        ]
        res = client.put(
            f"/v1/studies/{study_id}/matrix?path=input/thermal/series/{area_id}/{cluster_id}/series",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        res.raise_for_status()

        # We can check the modified matrix
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/thermal/series/{area_id}/{cluster_id}/series",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        actual = res.json()["data"]
        assert actual[1][0] == 128
        del actual[1]
        assert all(row[0] == 0 for row in actual)
