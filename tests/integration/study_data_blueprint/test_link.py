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

import pytest
from starlette.testclient import TestClient

from antarest.study.business.model.link_model import TransmissionCapacity
from tests.integration.prepare_proxy import PreparerProxy


@pytest.mark.unit_test
class TestLink:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_link_update(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        if pytest.FAST_MODE:
            pytest.skip("Skipping test")
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=820)
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "hurdlesCost": True, "comments": "comment"},
        )
        res = client.put(
            f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}",
            json={"colorr": 150},
        )

        assert res.status_code == 200
        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 150,
            "displayComments": True,
            "comments": "comment",
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": True,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        assert expected == res.json()

        # Test update link same area

        res = client.put(
            f"/v1/studies/{study_id}/links/{area1_id}/{area1_id}",
            json={"hurdlesCost": False},
        )
        assert res.status_code == 404
        expected = {
            "description": "The link area 1 -> area 1 is not present in the study",
            "exception": "LinkNotFound",
        }
        assert expected == res.json()

        # Test update link area not ordered

        res = client.put(
            f"/v1/studies/{study_id}/links/{area2_id}/{area1_id}",
            json={"hurdlesCost": False},
        )
        assert res.status_code == 200
        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 150,
            "displayComments": True,
            "comments": "comment",
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        assert expected == res.json()

        # Test update link with non existing area

        res = client.put(
            f"/v1/studies/{study_id}/links/{area1_id}/id_do_not_exist",
            json={"hurdlesCost": False},
        )
        assert res.status_code == 404
        expected = {
            "description": "The link area 1 -> id_do_not_exist is not present in the study",
            "exception": "LinkNotFound",
        }
        assert expected == res.json()

        # Test update link fails when given wrong parameters
        if study_type == "raw":
            res = client.post(
                f"/v1/studies/{study_id}/commands",
                json=[
                    {
                        "action": "update_link",
                        "args": {
                            "area1": area1_id,
                            "area2": area2_id,
                            "parameters": {"hurdles-cost": False, "wrong": "parameter"},
                        },
                    }
                ],
            )
            assert res.status_code == 422
            assert "Extra inputs are not permitted" in res.json()["description"]

        # Test update link variant returns only modified values

        if study_type == "variant":
            res = client.put(
                f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}",
                json={"hurdlesCost": False},
            )
            assert res.status_code == 200

            res = client.get(f"/v1/studies/{study_id}/commands")
            commands = res.json()
            command_args = commands[-1]["args"]
            assert command_args["parameters"] == {"hurdlesCost": False}

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_link_820(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=820)
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        area3_id = preparer.create_area(study_id, name="Area 3")["id"]

        # Test create link with default values
        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id})

        assert res.status_code == 200, res.json()

        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "displayComments": True,
            "comments": "",
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        assert expected == res.json()
        res = client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}")
        res.raise_for_status()

        # Test create link with parameters

        parameters = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 160,
            "colorg": 170,
            "colorr": 180,
            "displayComments": True,
            "comments": "comment",
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        res = client.post(
            f"/v1/studies/{study_id}/links",
            json=parameters,
        )

        assert res.status_code == 200, res.json()

        assert parameters == res.json()
        res = client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}")
        res.raise_for_status()

        # Create two links, count them, then delete one

        res1 = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id})
        res2 = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area3_id})

        assert res1.status_code == 200, res1.json()
        assert res2.status_code == 200, res2.json()

        res = client.get(f"/v1/studies/{study_id}/links")

        assert res.status_code == 200, res.json()
        assert 2 == len(res.json())

        res = client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area3_id}")
        res.raise_for_status()

        res = client.get(f"/v1/studies/{study_id}/links")

        assert res.status_code == 200, res.json()
        assert 1 == len(res.json())
        client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}")
        res.raise_for_status()

        # Test create link with same area

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area1_id})

        assert res.status_code == 422, res.json()
        expected = {
            "description": "Cannot create a link that goes from and to the same single area: area 1",
            "exception": "LinkValidationError",
        }
        assert expected == res.json()

        # Test create link with wrong value for enum

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "assetType": TransmissionCapacity.ENABLED},
        )
        assert res.status_code == 422, res.json()
        expected = {
            "body": {"area1": "area 1", "area2": "area 2", "assetType": "enabled"},
            "description": "Input should be 'ac', 'dc', 'gaz', 'virt' or 'other'",
            "exception": "RequestValidationError",
        }
        assert expected == res.json()

        # Test create link with wrong color parameter

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "colorr": 260})

        assert res.status_code == 422, res.json()
        expected = {
            "body": {"area1": "area 1", "area2": "area 2", "colorr": 260},
            "description": "Input should be less than or equal to 255",
            "exception": "RequestValidationError",
        }
        assert expected == res.json()

        # Test create link with wrong filter parameter

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "filterSynthesis": "centurial"},
        )

        assert res.status_code == 422, res.json()

        res_json = res.json()
        assert res_json["exception"] == "RequestValidationError"
        assert (
            res_json["description"]
            == "Value error, Invalid value(s) in filters: centurial. Allowed values are: annual, daily, hourly, monthly, weekly."
        )

        # Test create link with empty filters

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "filterSynthesis": ""},
        )

        assert res.status_code == 200, res.json()
        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "displayComments": True,
            "comments": "",
            "filterSynthesis": "",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        assert expected == res.json()

        # Test create link with double value in filter

        client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}")
        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "filterSynthesis": "hourly, hourly"},
        )

        assert res.status_code == 200, res.json()
        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "displayComments": True,
            "comments": "",
            "filterSynthesis": "hourly",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
        assert expected == res.json()
