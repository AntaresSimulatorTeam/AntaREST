from typing import List

import pytest
from http import HTTPStatus
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
        assert res.status_code == HTTPStatus.OK
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
        assert res.status_code == HTTPStatus.OK
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
            json=obj,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "de": {"[allocation]": {"de": 3.0, "es": 1.0}},
            "es": {"[allocation]": {"es": 1}},
            "fr": {"[allocation]": {"fr": 1}},
            "it": {"[allocation]": {"it": 1}},
        }
        assert actual == expected
