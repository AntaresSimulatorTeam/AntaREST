from http import HTTPStatus
from typing import List

import pytest
from antarest.study.business.area_management import AreaInfoDTO
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestHydroCorrelation:
    """
    Test the end points related to hydraulic correlation.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_correlation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `get_correlation_form_values` end point"""
        area_id = "fr"
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/correlation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "correlation": [
                {"areaId": "de", "coefficient": 25.0},
                {"areaId": "es", "coefficient": 75.0},
                {"areaId": "fr", "coefficient": 100.0},
                {"areaId": "it", "coefficient": 75.0},
            ]
        }
        assert actual == expected

    def test_set_correlation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `set_correlation_form_values` end point"""
        area_id = "fr"
        obj = {
            "correlation": [
                {"areaId": "de", "coefficient": 20},
                {"areaId": "es", "coefficient": -82.8},
                {"areaId": "it", "coefficient": 0},
                {"areaId": "fr", "coefficient": 100.0},
            ]
        }
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/correlation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "correlation": [
                {"areaId": "de", "coefficient": 20.0},
                {"areaId": "es", "coefficient": -82.8},
                {"areaId": "fr", "coefficient": 100.0},
            ]
        }
        assert actual == expected

        # check that the form is updated correctly
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/hydro/correlation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "correlation": [
                {"areaId": "de", "coefficient": 20.0},
                {"areaId": "es", "coefficient": -82.8},
                {"areaId": "fr", "coefficient": 100.0},
            ]
        }
        assert actual == expected

        # check that the matrix is symmetric
        res = client.get(
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "columns": ["de", "es", "fr", "it"],
            "data": [
                [1.0, 0.0, 0.2, 0.0],
                [0.0, 1.0, -0.828, 0.12],
                [0.2, -0.828, 1.0, 0.0],
                [0.0, 0.12, 0.0, 1.0],
            ],
            "index": ["de", "es", "fr", "it"],
        }
        assert actual == expected

    @pytest.mark.parametrize(
        "columns, expected",
        [
            pytest.param(
                "",
                {
                    "columns": ["de", "es", "fr", "it"],
                    "data": [
                        [1.0, 0.0, 0.25, 0.0],
                        [0.0, 1.0, 0.75, 0.12],
                        [0.25, 0.75, 1.0, 0.75],
                        [0.0, 0.12, 0.75, 1.0],
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
                        [1.0, 0.25],
                        [0.0, 0.75],
                        [0.25, 1.0],
                        [0.0, 0.75],
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
                        [0.25],
                        [0.75],
                        [1.0],
                        [0.75],
                    ],
                    "index": ["de", "es", "fr", "it"],
                },
                id="one-area",
            ),
        ],
    )
    def test_get_correlation_matrix(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
        columns: str,
        expected: List[List[float]],
    ):
        """Check `get_correlation_matrix` end point"""
        query = f"columns={columns}" if columns else ""
        res = client.get(
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix?{query}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual == expected

    def test_set_correlation_matrix(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ):
        """Check `set_correlation_matrix` end point"""
        obj = {
            "columns": ["fr", "it"],
            "data": [
                [-0.79332875, -0.96830414],
                [-0.23220568, -0.158783],
                [1.0, 0.82],
                [0.82, 1.0],
            ],
            "index": ["de", "es", "fr", "it"],
        }
        res = client.put(
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = obj
        assert actual == expected

        res = client.get(
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "columns": ["de", "es", "fr", "it"],
            "data": [
                [1.0, 0.0, -0.79332875, -0.96830414],
                [0.0, 1.0, -0.23220568, -0.158783],
                [-0.79332875, -0.23220568, 1.0, 0.82],
                [-0.96830414, -0.158783, 0.82, 1.0],
            ],
            "index": ["de", "es", "fr", "it"],
        }
        assert actual == expected

    def test_create_area(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when an area is created, the hydraulic correlation
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
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK
        actual = res.json()
        expected = {
            "columns": ["de", "es", "fr", "it", "north"],
            "data": [
                [1.0, 0.0, 0.25, 0.0, 0.0],
                [0.0, 1.0, 0.75, 0.12, 0.0],
                [0.25, 0.75, 1.0, 0.75, 0.0],
                [0.0, 0.12, 0.75, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            "index": ["de", "es", "fr", "it", "north"],
        }
        assert actual == expected

    def test_delete_area(
        self, client: TestClient, user_access_token: str, study_id: str
    ):
        """
        Given a study, when an area is deleted, the hydraulic correlation
        column for this area must be removed.
        Other columns must be updated to reflect the area deletion.
        """
        # First change the coefficients to avoid zero values (which are defaults).
        correlation_cfg = {
            "annual": {
                "de%es": 0.12,
                "de%fr": 0.13,
                "de%it": 0.14,
                "es%fr": 0.22,
                "es%it": 0.23,
                "fr%it": 0.32,
            }
        }
        res = client.post(
            f"/v1/studies/{study_id}/raw?path=input/hydro/prepro/correlation",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=correlation_cfg,
        )
        assert res.status_code == HTTPStatus.NO_CONTENT, res.json()

        # Then we remove the "fr" zone.
        # The deletion should update the correlation matrix of all other zones.
        res = client.delete(
            f"/v1/studies/{study_id}/areas/fr",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the "fr" column is removed from the hydraulic correlation matrix.
        # The row corresponding to "fr" must also be deleted.
        res = client.get(
            f"/v1/studies/{study_id}/areas/hydro/correlation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "columns": ["de", "es", "it"],
            "data": [
                [1.0, 0.12, 0.14],
                [0.12, 1.0, 0.23],
                [0.14, 0.23, 1.0],
            ],
            "index": ["de", "es", "it"],
        }
        assert actual == expected
