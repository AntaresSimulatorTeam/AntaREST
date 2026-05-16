# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


def _seed(client: TestClient, preparer: PreparerProxy) -> tuple[str, str, str]:
    study_id = preparer.create_study("thermal-reserve-participations", version=1000, storage_mode="database")
    area_id = "fr"
    preparer.create_area(study_id, name=area_id)

    cluster = preparer.create_thermal(study_id, area_id, name="gas_cluster")
    thermal_id = cluster["id"]

    for rid in ("Reserve 1", "Reserve 2"):
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/reserves",
            json={"id": rid, "type": "up"},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()

    return study_id, thermal_id, area_id


class TestThermalClusterReserveParticipations:
    def test_full_crud(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id, area_id = _seed(client, preparer)
        base = f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id}/reserves"

        res = client.get(base, headers=preparer.headers)
        assert res.status_code == 200, res.json()
        assert res.json() == []

        res = client.post(
            base,
            json={"id": "Reserve 1", "maxPower": 20.0, "participationCost": 1.5},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body = res.json()
        assert body["id"] == "Reserve 1"
        assert body["maxPower"] == 20.0
        assert body["participationCost"] == 1.5
        assert body["maxPowerOff"] == 0.0
        assert body["participationCostOff"] == 0.0

        res = client.post(
            base,
            json={"id": "Reserve 2", "maxPower": 5.0},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()

        res = client.get(base, headers=preparer.headers)
        assert res.status_code == 200
        listing = res.json()
        assert {p["id"] for p in listing} == {"Reserve 1", "Reserve 2"}

        res = client.get(f"{base}/Reserve 1", headers=preparer.headers)
        assert res.status_code == 200
        assert res.json()["maxPower"] == 20.0

        res = client.patch(
            f"{base}/Reserve 1",
            json={"maxPower": 99.0},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        updated = res.json()
        assert updated["maxPower"] == 99.0
        assert updated["participationCost"] == 1.5

        res = client.request(
            "DELETE",
            base,
            json=["Reserve 1"],
            headers=preparer.headers,
        )
        assert res.status_code == 204, res.text

        res = client.get(f"{base}/Reserve 1", headers=preparer.headers)
        assert res.status_code == 404, res.json()

        res = client.get(f"{base}/Reserve 2", headers=preparer.headers)
        assert res.status_code == 200

    def test_create_unknown_reserve_returns_error(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id, area_id = _seed(client, preparer)

        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id}/reserves",
            json={"id": "ghost", "maxPower": 1.0},
            headers=preparer.headers,
        )
        assert res.status_code in (400, 422, 500), res.json()
        if res.status_code == 500:
            assert "ghost" in res.text or "Reserve" in res.text

    def test_get_not_found(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id, area_id = _seed(client, preparer)

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id}/reserves/ghost",
            headers=preparer.headers,
        )
        assert res.status_code == 404, res.json()

    def test_cascade_on_thermal_delete(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id, area_id = _seed(client, preparer)
        base = f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id}/reserves"

        client.post(base, json={"id": "Reserve 1"}, headers=preparer.headers).raise_for_status()

        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            json=[thermal_id],
            headers=preparer.headers,
        )
        assert res.status_code in (200, 204), res.text

        cluster = preparer.create_thermal(study_id, area_id, name="gas_cluster")
        new_thermal_id = cluster["id"]
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{new_thermal_id}/reserves",
            headers=preparer.headers,
        )
        assert res.status_code == 200
        assert res.json() == []

    def test_cascade_on_reserve_definition_delete(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id, area_id = _seed(client, preparer)
        base = f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id}/reserves"

        client.post(base, json={"id": "Reserve 1"}, headers=preparer.headers).raise_for_status()
        client.post(base, json={"id": "Reserve 2"}, headers=preparer.headers).raise_for_status()

        # Delete reserve definition R1 — its participation should be gone.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/reserves",
            json=["Reserve 1"],
            headers=preparer.headers,
        )
        assert res.status_code == 204, res.text

        res = client.get(base, headers=preparer.headers)
        assert res.status_code == 200
        listing = res.json()
        assert {p["id"] for p in listing} == {"Reserve 2"}

    def test_two_clusters_share_same_reserve(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)
        study_id, thermal_id_1, area_id = _seed(client, preparer)
        cluster_2 = preparer.create_thermal(study_id, area_id, name="coal_cluster")
        thermal_id_2 = cluster_2["id"]

        base_1 = f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id_1}/reserves"
        base_2 = f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{thermal_id_2}/reserves"

        res = client.post(
            base_1,
            json={"id": "Reserve 1", "maxPower": 20.0, "participationCost": 1.0},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        res = client.post(
            base_2,
            json={"id": "Reserve 1", "maxPower": 30.0, "participationCost": 2.0},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()

        body_1 = client.get(f"{base_1}/Reserve 1", headers=preparer.headers).json()
        body_2 = client.get(f"{base_2}/Reserve 1", headers=preparer.headers).json()
        assert body_1["maxPower"] == 20.0
        assert body_1["participationCost"] == 1.0
        assert body_2["maxPower"] == 30.0
        assert body_2["participationCost"] == 2.0

        res = client.patch(
            f"{base_1}/Reserve 1",
            json={"maxPower": 99.0},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body_2_again = client.get(f"{base_2}/Reserve 1", headers=preparer.headers).json()
        assert body_2_again["maxPower"] == 30.0

        client.request("DELETE", base_1, json=["Reserve 1"], headers=preparer.headers).raise_for_status()
        assert client.get(f"{base_1}/Reserve 1", headers=preparer.headers).status_code == 404
        assert client.get(f"{base_2}/Reserve 1", headers=preparer.headers).status_code == 200
