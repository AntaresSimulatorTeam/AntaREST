# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
from http import HTTPStatus
from unittest.mock import ANY

import pytest
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestHydroInflowProperties:
    """
    Test the end points related to hydraulic inflow-structure.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_inflow_properties(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        user_header = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # ====================
        # Use case : RAW study
        # ====================

        # Check that the default values are returned
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.5}
        assert actual == expected

        # Update the values
        obj = {"interMonthlyCorrelation": 0.8}
        res = client.put(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the right values are returned
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure",
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
            f"/v1/studies/{internal_study_id}/copy",
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
            "action": "update_inflow_properties",
            "args": {"area_id": "fr", "properties": {"inter_monthly_correlation": 0.9}},
            "version": 1,
            "updated_at": ANY,
            "user_name": ANY,
        }
        assert actual[1] == expected

    def test_update_inflow_structure__invalid_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        user_header = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # Update the values with invalid values
        obj = {"interMonthlyCorrelation": 1.1}
        res = client.put(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()

        obj = {"interMonthlyCorrelation": -0.1}
        res = client.put(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure",
            headers=user_header,
            json=obj,
        )
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
