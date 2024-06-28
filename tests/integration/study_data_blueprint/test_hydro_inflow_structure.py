from http import HTTPStatus
from unittest.mock import ANY

import pytest
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestHydroInflowStructure:
    """
    Test the end points related to hydraulic inflow-structure.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_inflow_structure(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study: str,
    ):
        user_header = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # ====================
        # Use case : RAW study
        # ====================

        # Check that the default values are returned
        res = client.get(
            f"/v1/studies/{internal_study}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.5}
        assert actual == expected

        # Update the values
        obj = {"interMonthlyCorrelation": 0.8}
        res = client.put(
            f"/v1/studies/{internal_study}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the right values are returned
        res = client.get(
            f"/v1/studies/{internal_study}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.8}
        assert actual == expected

        # ========================
        # Use case : Variant study
        # ========================

        # Create a managed study from the RAW study.
        res = client.post(
            f"/v1/studies/{internal_study}/copy",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"dest": "Clone", "with_outputs": False, "use_task": False},
        )
        res.raise_for_status()
        managed_id = res.json()
        assert managed_id is not None

        # Create a variant from the managed study.
        res = client.post(
            f"/v1/studies/{managed_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": "Variant"},
        )
        res.raise_for_status()
        variant_id = res.json()
        assert variant_id is not None

        # Check that the return values match the RAW study values
        res = client.get(
            f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.8}
        assert actual == expected

        # Update the values
        obj = {"interMonthlyCorrelation": 0.9}
        res = client.put(
            f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the right values are returned
        res = client.get(
            f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.9}
        assert actual == expected

        # Check the variant commands
        res = client.get(
            f"/v1/studies/{variant_id}/commands",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert len(actual) == 2
        expected = {
            "id": ANY,
            "action": "update_config",
            "args": {
                "target": "input/hydro/prepro/fr/prepro/prepro",
                "data": {"intermonthly-correlation": 0.9},
            },
            "version": 1,
        }
        assert actual[1] == expected

    def test_update_inflow_structure__invalid_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study: str,
    ):
        user_header = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # Update the values with invalid values
        obj = {"interMonthlyCorrelation": 1.1}
        res = client.put(
            f"/v1/studies/{internal_study}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()

        obj = {"interMonthlyCorrelation": -0.1}
        res = client.put(
            f"/v1/studies/{internal_study}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
