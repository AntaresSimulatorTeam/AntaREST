from http import HTTPStatus
from typing import List

import pytest
from antarest.study.business.area_management import AreaInfoDTO
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestHydroAllocation:
    """
    Test the end points related to hydraulic allocation.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_allocation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `get_allocation_form_values` end point"""
        area_id = "de"
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/allocation",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"allocation": [{"areaId": "de", "coefficient": 1.0}]}
        assert actual == expected

    @pytest.mark.parametrize(
        "area_id, expected",
        [
            pytest.param(
                "*",
                {
                    "columns": ["de", "es", "fr", "it"],
                    "data": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ],
                    "index": ["de", "es", "fr", "it"],
                },
                id="all-areas",
            ),
            pytest.param(
                "fr,de",
                {
                    "columns": ["de", "fr"],
                    "data": [
                        [1.0, 0.0],
                        [0.0, 0.0],
                        [0.0, 1.0],
                        [0.0, 0.0],
                    ],
                    "index": ["de", "es", "fr", "it"],
                },
                id="some-areas",
            ),
            pytest.param(
                "fr",
                {
                    "columns": ["fr"],
                    "data": [
                        [0.0],
                        [0.0],
                        [1.0],
                        [0.0],
                    ],
                    "index": ["de", "es", "fr", "it"],
                },
                id="one-area",
            ),
        ],
    )
    def test_get_allocation_matrix(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        area_id: str,
        expected: List[List[float]],
    ):
        """Check `get_allocation_matrix` end point"""
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/allocation.df",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual == expected

    def test_set_allocation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `set_allocation_form_values` end point"""
        area_id = "de"
        obj = {
            "allocation": [
                {"areaId": "de", "coefficient": 3},
                {"areaId": "es", "coefficient": 1.0},
            ]
        }
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/allocation",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        assert res.status_code == HTTPStatus.NO_CONTENT, res.json()
        actual = res.json()
        assert not actual

        # check that the values are updated
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/hydro/allocation&depth=3",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "de": {"[allocation]": {"de": 3.0, "es": 1.0}},
            "es": {"[allocation]": {"es": 1}},
            "fr": {"[allocation]": {"fr": 1}},
            "it": {"[allocation]": {"it": 1}},
        }
        assert actual == expected

    def test_create_area(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when an area is created, the hydraulic allocation
        column for this area must be updated with the following values:
        - the coefficient == 1 for this area,
        - the coefficient == 0 for the other areas.
        Other columns must not be changed.
        """
        area_info = AreaInfoDTO(id="north", name="NORTH", type="AREA")
        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
            data=area_info.json(),
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/areas/*/hydro/allocation.df",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK
        actual = res.json()
        expected = {
            "columns": ["de", "es", "fr", "it", "north"],
            "data": [
                [1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            "index": ["de", "es", "fr", "it", "north"],
        }
        assert actual == expected

    def test_delete_area(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when an area is deleted, the hydraulic allocation
        column for this area must be removed.
        Other columns must be updated to reflect the area deletion.
        """
        # First change the coefficients to avoid zero values (which are defaults).
        obj = {
            "de": {"[allocation]": {"de": 10, "es": 20, "fr": 30, "it": 40}},
            "es": {"[allocation]": {"de": 11, "es": 21, "fr": 31, "it": 41}},
            "fr": {"[allocation]": {"de": 12, "es": 22, "fr": 32, "it": 42}},
            "it": {"[allocation]": {"de": 13, "es": 23, "fr": 33, "it": 43}},
        }
        for prod_area, allocation_cfg in obj.items():
            res = client.post(
                f"/v1/studies/{study_id}/raw?path=input/hydro/allocation/{prod_area}",
                headers={"Authorization": f"Bearer {user_access_token}"},
                json=allocation_cfg,
            )
            assert res.status_code == HTTPStatus.NO_CONTENT, res.json()

        # Then we remove the "fr" zone.
        # The deletion should update the allocation matrix of all other zones.
        res = client.delete(
            f"/v1/studies/{study_id}/areas/fr",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the "fr" column is removed from the hydraulic allocation matrix.
        # The row corresponding to "fr" must also be deleted.
        res = client.get(
            f"/v1/studies/{study_id}/areas/*/hydro/allocation.df",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "columns": ["de", "es", "it"],
            "data": [
                [10.0, 11.0, 13.0],
                [20.0, 21.0, 23.0],
                [40.0, 41.0, 43.0],
            ],
            "index": ["de", "es", "it"],
        }
        assert actual == expected
