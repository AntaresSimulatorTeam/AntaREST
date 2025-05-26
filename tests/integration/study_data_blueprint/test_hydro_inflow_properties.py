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
import copy
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
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # ====================
        # Use case : RAW study
        # ====================

        # Check that the default values are returned
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure")
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.5}
        assert actual == expected

        # Update the values
        obj = {"interMonthlyCorrelation": 0.8}
        res = client.put(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure", json=obj)
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the right values are returned
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure")
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
            params={"study_name": "Clone", "with_outputs": False, "use_task": False},
        )
        res.raise_for_status()
        managed_id = res.json()
        assert managed_id is not None

        # Create a variant from the managed study.
        res = client.post(f"/v1/studies/{managed_id}/variants", params={"name": "Variant"})
        res.raise_for_status()
        variant_id = res.json()
        assert variant_id is not None

        # Check that the return values match the RAW study values
        res = client.get(f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure")
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.8}
        assert actual == expected

        # Update the values
        obj = {"interMonthlyCorrelation": 0.9}
        res = client.put(f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure", json=obj)
        assert res.status_code == HTTPStatus.OK, res.json()

        # Check that the right values are returned
        res = client.get(f"/v1/studies/{variant_id}/areas/{area_id}/hydro/inflow-structure")
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"interMonthlyCorrelation": 0.9}
        assert actual == expected

        # Check the variant commands
        res = client.get(f"/v1/studies/{variant_id}/commands")
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert len(actual) == 2
        expected = {
            "id": ANY,
            "action": "update_inflow_structure",
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
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        area_id = "fr"

        # Update the values with invalid values
        obj = {"interMonthlyCorrelation": 1.1}
        res = client.put(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure", json=obj)
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()

        obj = {"interMonthlyCorrelation": -0.1}
        res = client.put(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/inflow-structure", json=obj)
        assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, res.json()

    def test_get_all_hydro_properties_inside_study(self, client: TestClient, user_access_token: str):
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.post("/v1/studies", params={"name": "test_study", "version": "8.8"})
        study_id = res.json()
        area_id = "fr"
        client.post(f"/v1/studies/{study_id}/areas", json={"name": area_id, "type": "AREA"})
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "be", "type": "AREA"})

        # Check default values
        res = client.get(f"/v1/studies/{study_id}/hydro")
        assert res.status_code == HTTPStatus.OK, res.json()
        default_properties = {
            "inflowStructure": {"interMonthlyCorrelation": 0.5},
            "managementOptions": {
                "followLoad": True,
                "hardBounds": False,
                "initializeReservoirDate": 0,
                "interDailyBreakdown": 1.0,
                "interMonthlyBreakdown": 1.0,
                "intraDailyModulation": 24.0,
                "leewayLow": 1.0,
                "leewayUp": 1.0,
                "powerToLevel": False,
                "pumpingEfficiency": 1.0,
                "reservoir": False,
                "reservoirCapacity": 0.0,
                "useHeuristic": True,
                "useLeeway": False,
                "useWater": False,
            },
        }
        assert res.json() == {"be": default_properties, "fr": default_properties}

        # Update inflow structure values
        obj = {"interMonthlyCorrelation": 0.8}
        res = client.put(f"/v1/studies/{study_id}/areas/{area_id}/hydro/inflow-structure", json=obj)
        assert res.status_code == HTTPStatus.OK, res.json()

        # Update hydro management properties
        obj = {"reservoirCapacity": 15}
        res = client.put(f"/v1/studies/{study_id}/areas/{area_id}/hydro/form", json=obj)
        assert res.status_code == HTTPStatus.OK, res.json()

        # Asserts properties were modified correctly
        res = client.get(f"/v1/studies/{study_id}/hydro")
        assert res.status_code == HTTPStatus.OK, res.json()
        new_fr_properties = copy.deepcopy(default_properties)
        new_fr_properties["managementOptions"]["reservoirCapacity"] = 15
        new_fr_properties["inflowStructure"]["interMonthlyCorrelation"] = 0.8
        assert res.json() == {"be": default_properties, "fr": new_fr_properties}
