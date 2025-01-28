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

import pytest
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


@pytest.mark.unit_test
class TestLink:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_nominal_case(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        # =============================
        #  SET UP
        # =============================

        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo")
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        links_url = f"/v1/studies/{study_id}/links"

        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        area3_id = preparer.create_area(study_id, name="Area 3")["id"]

        # =============================
        #  CREATION AND UPDATE
        # =============================

        # Link creation with default values
        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id})

        assert res.status_code == 200, res.json()

        default_parameters = {
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
            "volatilityForced": 0.0,
            "volatilityPlanned": 0.0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
            "forceNoGeneration": True,
            "nominalCapacity": 0.0,
            "unitCount": 1,
        }
        expected_result = copy.deepcopy(default_parameters)
        expected_result["area1"] = area1_id
        expected_result["area2"] = area2_id
        assert res.json() == expected_result

        # Link creation with specific values and then updates another value
        client.post(
            links_url,
            json={"area1": area1_id, "area2": area3_id, "hurdlesCost": True, "comments": "comment"},
        )
        res = client.put(f"/v1/studies/{study_id}/links/{area1_id}/{area3_id}", json={"colorr": 150})
        assert res.status_code == 200
        expected = copy.deepcopy(default_parameters)
        expected["area1"] = area1_id
        expected["area2"] = area3_id
        expected["hurdlesCost"] = True
        expected["comments"] = "comment"
        expected["colorr"] = 150
        assert res.json() == expected

        # Test update link area not ordered

        res = client.put(f"/v1/studies/{study_id}/links/{area3_id}/{area1_id}", json={"hurdlesCost": False})
        assert res.status_code == 200
        expected["hurdlesCost"] = False
        assert res.json() == expected

        # Test update link variant returns only modified values

        if study_type == "variant":
            res = client.put(
                f"/v1/studies/{study_id}/links/{area1_id}/{area3_id}",
                json={"assetType": "dc"},
            )
            assert res.status_code == 200

            res = client.get(f"/v1/studies/{study_id}/commands")
            commands = res.json()
            command_args = commands[-1]["args"]
            assert command_args["parameters"] == {"asset_type": "dc"}

        # Test create link with empty filters

        res = client.post(links_url, json={"area1": area2_id, "area2": area3_id, "filterSynthesis": ""})
        assert res.status_code == 200, res.json()
        expected = copy.deepcopy(default_parameters)
        expected["area1"] = area2_id
        expected["area2"] = area3_id
        expected["filterSynthesis"] = ""
        assert res.json() == expected
        res = client.delete(f"/v1/studies/{study_id}/links/{area2_id}/{area3_id}")
        res.raise_for_status()

        # Test create link with double value in filter

        res = client.post(links_url, json={"area1": area2_id, "area2": area3_id, "filterSynthesis": "hourly, hourly"})
        assert res.status_code == 200, res.json()
        expected = copy.deepcopy(default_parameters)
        expected["filterSynthesis"] = "hourly"
        expected["area1"] = area2_id
        expected["area2"] = area3_id
        assert res.json() == expected

        # =============================
        #  DELETION
        # =============================

        # Deletes one link and asserts it's not present anymore
        res = client.get(links_url)
        assert res.status_code == 200, res.json()
        assert 3 == len(res.json())

        res = client.delete(f"/v1/studies/{study_id}/links/{area2_id}/{area3_id}")
        assert res.status_code == 200, res.json()

        res = client.get(links_url)
        assert res.status_code == 200
        assert 2 == len(res.json())

        # =============================
        #  ERRORS
        # =============================

        # Test update link same area

        res = client.put(f"/v1/studies/{study_id}/links/{area1_id}/{area1_id}", json={"hurdlesCost": False})
        assert res.status_code == 422
        assert res.json()["description"] == "Cannot create a link that goes from and to the same single area: area 1"
        assert res.json()["exception"] == "LinkValidationError"

        # Test update link with non-existing area

        res = client.put(f"/v1/studies/{study_id}/links/{area1_id}/id_do_not_exist", json={"hurdlesCost": False})
        assert res.status_code == 404
        assert res.json()["description"] == "The link area 1 -> id_do_not_exist is not present in the study"
        assert res.json()["exception"] == "LinkNotFound"

        # Test create link with wrong value for enum

        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id, "assetType": "enabled"})
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == "Input should be 'ac', 'dc', 'gaz', 'virt' or 'other'"
        assert res.json()["exception"] == "RequestValidationError"

        # Test create link with wrong color parameter

        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id, "colorr": 260})
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == "Input should be less than or equal to 255"
        assert res.json()["exception"] == "RequestValidationError"

        # Test create link with wrong filter parameter

        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id, "filterSynthesis": "centurial"})
        assert res.status_code == 422, res.json()
        expected = {
            "description": "Invalid value(s) in filters: centurial. Allowed values are: hourly, daily, weekly, monthly, annual.",
            "exception": "LinkValidationError",
        }
        assert expected == res.json()

        # Test update link command fails when given wrong parameters

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
            assert res.status_code == 500
            expected = "Unexpected exception occurred when trying to apply command CommandName.UPDATE_LINK"
            assert expected in res.json()["description"]

    def test_other_behaviors(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=810)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        links_url = f"/v1/studies/{study_id}/links"

        # Asserts we cannot give a filter value to a study prior to v8.2
        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id, "filterSynthesis": "hourly"})
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == "Cannot specify a filter value for study's version earlier than v8.2"
        assert res.json()["exception"] == "LinkValidationError"

        # =============================
        #  TS GENERATION
        # =============================

        # Creates a link inside parent study with a specific unit count
        res = client.post(links_url, json={"area1": area1_id, "area2": area2_id, "unitCount": 24})
        assert res.status_code == 200, res.json()
        # Asserts the value was saved correctly
        res = client.get(links_url)
        assert res.json()[0]["unitCount"] == 24
        # Creates a variant
        variant_id = preparer.create_variant(study_id, name="Variant 1")
        # Asserts we still have the parent value
        res = client.get(f"/v1/studies/{variant_id}/links")
        assert res.json()[0]["unitCount"] == 24
        # Modifies the unitCount value. The command is only appended not applied so the data isn't saved in DB
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            json=[
                {
                    "action": "update_link",
                    "args": {
                        "area1": area1_id,
                        "area2": area2_id,
                        "parameters": {"unit-count": 12},
                    },
                }
            ],
        )
        assert res.status_code == 200, res.json()
        # Creates a variant of level 2
        level_2_variant_id = preparer.create_variant(variant_id, name="Variant 2")
        # Asserts we see the right value
        res = client.get(f"/v1/studies/{level_2_variant_id}/links")
        assert res.json()[0]["unitCount"] == 12
