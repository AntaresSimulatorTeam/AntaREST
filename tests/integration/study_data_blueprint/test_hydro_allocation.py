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

    @pytest.mark.parametrize(
        "obj, detail",
        [
            pytest.param(
                {"allocation": []},
                [
                    {
                        "loc": ["body", "allocation"],
                        "msg": "coefficients array is empty",
                        "type": "value_error",
                    }
                ],
                id="at-least-1-area",
            ),
            pytest.param(
                {"allocation": [{"areaId": "de", "coefficient": -5}]},
                [
                    {
                        "loc": ["body", "allocation", 0, "coefficient"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                        "ctx": {"limit_value": 0},
                    }
                ],
                id="non-positive-number",
            ),
            pytest.param(
                {"allocation": [{"areaId": "de", "coefficient": 0}]},
                [
                    {
                        "loc": ["body", "allocation"],
                        "msg": "coefficients array has no non-null values",
                        "type": "value_error",
                    }
                ],
                id="nul-allocation-table1",
            ),
            pytest.param(
                {
                    "allocation": [
                        {"areaId": "de", "coefficient": 0},
                        {"areaId": "fr", "coefficient": 0},
                    ]
                },
                [
                    {
                        "loc": ["body", "allocation"],
                        "msg": "coefficients array has no non-null values",
                        "type": "value_error",
                    }
                ],
                id="nul-allocation-table2",
            ),
            # fmt: on
        ],
    )
    def test_update_unprocessable_entity(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        obj: dict,
        detail: list,
    ):
        area_id = "de"
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/allocation",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        actual = res.json()
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, actual
        assert actual == {"detail": detail}

    @pytest.mark.parametrize(
        "obj, expected",
        [
            pytest.param(
                {"allocation": [{"areaId": "MISSING", "coefficient": 3}]},
                {
                    "description": "1 area is not found: 'MISSING'",
                    "exception": "AreaNotFound",
                },
                id="UNKNOWN-area",
            ),
            pytest.param(
                {
                    "allocation": [
                        {"areaId": "MISSING1", "coefficient": 1},
                        {"areaId": "MISSING2", "coefficient": 2},
                        {"areaId": "fr", "coefficient": 3},
                    ]
                },
                {
                    "description": "2 areas are not found: 'MISSING1', 'MISSING2'",
                    "exception": "AreaNotFound",
                },
                id="UNKNOWN-areas",
            ),
        ],
    )
    def test_update_not_found(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        obj: dict,
        expected: dict,
    ):
        area_id = "de"
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/allocation",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        actual = res.json()
        assert res.status_code == HTTPStatus.NOT_FOUND, actual
        assert actual == expected
