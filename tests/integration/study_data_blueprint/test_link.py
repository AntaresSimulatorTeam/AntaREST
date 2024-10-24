# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from sys import stderr

import pytest
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.model.filesystem.config.links import TransmissionCapacity
from tests.integration.prepare_proxy import PreparerProxy


@pytest.mark.unit_test
class TestLink:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_link_update(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=820)
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "hurdles-cost": True})
        res = client.put(
            f"/v1/studies/{study_id}/links",
            json={
                "area1": area1_id,
                "area2": area2_id,
                "hurdles-cost": False,
                "colorr": 150,
                "filter-synthesis": "hourly",
            },
        )

        assert res.status_code == 200
        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "asset-type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 150,
            "display-comments": True,
            "filter-synthesis": "hourly",
            "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
            "hurdles-cost": False,
            "link-style": "plain",
            "link-width": 1.0,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": False,
        }
        assert expected == res.json()

        # Test update link same area

        res = client.put(
            f"/v1/studies/{study_id}/links",
            json={
                "area1": area1_id,
                "area2": area1_id,
                "hurdles-cost": False,
            },
        )
        assert res.status_code == 422
        expected = {"description": "Area 1 and Area 2 can not be the same", "exception": "LinkValidationError"}
        assert expected == res.json()

        # Test update link with non existing area

        res = client.put(
            f"/v1/studies/{study_id}/links",
            json={
                "area1": area1_id,
                "area2": "id_do_not_exist",
                "hurdles-cost": False,
            },
        )
        assert res.status_code == 422
        expected = {
            "description": "The link area 1 -> id_do_not_exist is not present in the study",
            "exception": "LinkValidationError",
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
            assert res.status_code == 500
            expected = {
                "description": "Unexpected exception occurred when trying to apply command CommandName.UPDATE_LINK: 1 validation error for LinkProperties\nwrong\n  Extra inputs are not permitted [type=extra_forbidden, input_value='parameter', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.8/v/extra_forbidden",
                "exception": "CommandApplicationError",
            }
            assert expected == res.json()

        # Test update link variant returns only modified values

        if study_type == "variant":
            res = client.put(
                f"/v1/studies/{study_id}/links",
                json={
                    "area1": area1_id,
                    "area2": area2_id,
                    "hurdles-cost": False,
                },
            )
            assert res.status_code == 200

            res = client.get(f"/v1/studies/{study_id}/commands")
            commands = res.json()
            command_args = commands[-1]["args"]
            assert command_args["parameters"] == {"hurdles-cost": False}

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
            "asset-type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display-comments": True,
            "filter-synthesis": "hourly, daily, weekly, monthly, annual",
            "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
            "hurdles-cost": False,
            "link-style": "plain",
            "link-width": 1.0,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": False,
        }
        assert expected == res.json()
        res = client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area2_id}")
        res.raise_for_status()

        # Test create link with parameters

        parameters = {
            "area1": area1_id,
            "area2": area2_id,
            "asset-type": "dc",
            "colorb": 160,
            "colorg": 170,
            "colorr": 180,
            "display-comments": True,
            "filter-synthesis": "hourly",
            "hurdles-cost": True,
            "link-style": "plain",
            "link-width": 2.0,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": True,
        }
        res = client.post(
            f"/v1/studies/{study_id}/links",
            json=parameters,
        )

        assert res.status_code == 200, res.json()
        parameters["filter-year-by-year"] = "hourly, daily, weekly, monthly, annual"

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
        expected = {"description": "Cannot create link on same area: area 1", "exception": "LinkValidationError"}
        assert expected == res.json()

        # Test create link with wrong value for enum

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area1_id, "asset-type": TransmissionCapacity.ENABLED},
        )
        assert res.status_code == 422, res.json()
        expected = {
            "body": {"area1": "area 1", "area2": "area 1", "asset-type": "enabled"},
            "description": "Input should be 'ac', 'dc', 'gaz', 'virt' or 'other'",
            "exception": "RequestValidationError",
        }
        assert expected == res.json()

        # Test create link with wrong color parameter

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "colorr": 260})

        assert res.status_code == 422, res.json()
        expected = {
            "body": {"area1": "area 1", "area2": "area 2", "colorr": 260},
            "description": "Input should be less than 255",
            "exception": "RequestValidationError",
        }
        assert expected == res.json()

        # Test create link with wrong filter parameter

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={"area1": area1_id, "area2": area2_id, "filter-synthesis": "centurial"},
        )

        assert res.status_code == 422, res.json()
        expected = {
            "description": "Invalid value(s) in filters: centurial. Allowed values are: hourly, daily, weekly, monthly, annual.",
            "exception": "LinkValidationError",
        }
        assert expected == res.json()

    def test_create_link_810(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=810)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        res = client.post(
            f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "filter-synthesis": "hourly"}
        )

        assert res.status_code == 422, res.json()
        expected = {
            "description": "Cannot specify a filter value for study's version earlier than v8.2",
            "exception": "LinkValidationError",
        }
        assert expected == res.json()
