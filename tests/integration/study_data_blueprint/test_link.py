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

import pytest
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy

# check error filter and version > 820

@pytest.mark.unit_test
class TestLink:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_with_default_value(
        self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

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

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_with_parameters(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        res = client.post(
            f"/v1/studies/{study_id}/links",
            json={
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
            },
        )

        assert res.status_code == 200, res.json()

        expected = {
            "area1": "area 1",
            "area2": "area 2",
            "asset-type": "dc",
            "colorb": 160,
            "colorg": 170,
            "colorr": 180,
            "display-comments": True,
            "filter-synthesis": "hourly",
            "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
            "hurdles-cost": True,
            "link-style": "plain",
            "link-width": 2.0,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": True,
        }
        assert expected == res.json()

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_two_links_and_count_then_delete_one(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        area3_id = preparer.create_area(study_id, name="Area 3")["id"]

        res1 = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id})
        res2 = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area3_id})

        assert res1.status_code == 200, res1.json()
        assert res2.status_code == 200, res2.json()

        res3 = client.get(f"/v1/studies/{study_id}/links")

        assert res3.status_code == 200, res3.json()
        assert 2 == len(res3.json())

        res4 = client.delete(f"/v1/studies/{study_id}/links/{area1_id}/{area3_id}")
        assert res4.status_code == 200, res4.json()

        res5 = client.get(f"/v1/studies/{study_id}/links")

        assert res5.status_code == 200, res5.json()
        assert 1 == len(res5.json())

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_with_same_area(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area1_id})

        assert res.status_code == 500, res.json()

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_already_existing_link(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id})
        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id})

        assert res.status_code == 500, res.json()

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_wrong_parameter_color(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "colorr": 260})

        assert res.status_code == 422, res.json()

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_wrong_parameter_filter(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "filter-synthesis": "centurial"})

        assert res.status_code == 500, res.json()

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_link_with_wrong_parameter_for_version_810(
            self, client: TestClient, user_access_token: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=810)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]

        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": area1_id, "area2": area2_id, "filter-synthesis": "hourly"})

        assert res.status_code == 500, res.json()