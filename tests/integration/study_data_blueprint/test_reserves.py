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

"""
## End-to-end tests of the reserve management endpoints.

Covers the endpoints defined in `study_data_blueprint.py` for:
* reserves global parameters (`/areas/{area_id}/reserves/global-parameters`)
* reserve definitions CRUD (`/areas/{area_id}/reserves[/{reserve_id}]`)
* thermal reserve symmetries/certifications (`/areas/{area_id}/reserves/symmetries|certifications/thermals`)
* short-term storage reserve symmetries/certifications
  (`/areas/{area_id}/reserves/symmetries|certifications/storages`)

Reserve definitions, global parameters and symmetries require study version >= 10.2.
Certifications (thermal and short-term storage) require study version >= 10.2.
"""

import http

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


def _create_study(client: TestClient, user_access_token: str, name: str, target_version: str) -> str:
    """Create a new empty study (v9.3) and upgrade it to the given target version (e.g. "1020")."""
    res = client.post("/v1/studies", params={"name": name, "version": 930})
    assert res.status_code in {200, 201}, res.json()
    study_id = res.json()

    res = client.put(f"/v1/studies/{study_id}/upgrade", params={"target_version": target_version})
    assert res.status_code == http.HTTPStatus.OK, res.json()
    task_id = res.json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED, task

    return study_id


@pytest.fixture
def study_id(client: TestClient, user_access_token: str) -> str:
    """A managed raw study in version 10.2, with one area "FR" containing 1 thermal cluster and 1 storage."""
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    study_id = _create_study(client, user_access_token, "MyStudy", "1020")

    res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "FR", "type": "AREA"})
    assert res.status_code in {200, 201}, res.json()
    area_id = res.json()["id"]
    assert area_id == "fr"

    res = client.post(
        f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
        json={"name": "Cluster 1", "group": "Other 1"},
    )
    assert res.status_code in {200, 201}, res.json()

    res = client.post(
        f"/v1/studies/{study_id}/areas/{area_id}/storages",
        json={"name": "Storage 1"},
    )
    assert res.status_code in {200, 201}, res.json()

    return study_id


class TestReservesGlobalParameters:
    def test_get_and_set_reserves_global_parameters(self, client: TestClient, study_id: str) -> None:
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/global-parameters")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {
            "referenceActivationDurationUp": 1,
            "energyActivationRatioUp": 1.0,
            "referenceActivationDurationDown": 1,
            "energyActivationRatioDown": 1.0,
        }

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/global-parameters",
            json={"referenceActivationDurationUp": 5, "energyActivationRatioDown": 0.5},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {
            "referenceActivationDurationUp": 5,
            "energyActivationRatioUp": 1.0,
            "referenceActivationDurationDown": 1,
            "energyActivationRatioDown": 0.5,
        }

        # Ensures the update was persisted
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/global-parameters")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json()["referenceActivationDurationUp"] == 5
        assert res.json()["energyActivationRatioDown"] == 0.5

    def test_reserves_global_parameters_wrong_area(self, client: TestClient, study_id: str) -> None:
        res = client.get(f"/v1/studies/{study_id}/areas/fake_area/reserves/global-parameters")
        assert res.status_code == http.HTTPStatus.NOT_FOUND, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fake_area/reserves/global-parameters",
            json={"referenceActivationDurationUp": 5},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_area" in res.json()["description"]

    def test_reserves_global_parameters_wrong_study_version(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.post("/v1/studies", params={"name": "OldStudy", "version": 930})
        assert res.status_code in {200, 201}, res.json()
        old_study_id = res.json()

        res = client.post(f"/v1/studies/{old_study_id}/areas", json={"name": "FR", "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"/v1/studies/{old_study_id}/areas/fr/reserves/global-parameters",
            json={"referenceActivationDurationUp": 5},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"


class TestReserveDefinitions:
    def test_lifecycle_nominal(self, client: TestClient, study_id: str) -> None:
        # No reserve definitions at first.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == []

        # Create a reserve with only a name (other properties get default values).
        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"name": "Reserve Up 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        created = res.json()
        assert created["id"] == "reserve up 1"
        assert created["name"] == "Reserve Up 1"
        assert created["type"] == "up"
        assert created["failureCost"] == 0.0
        assert created["spillageCost"] == 0.0
        assert created["referenceActivationDuration"] == 1
        assert created["powerActivationRatio"] == 0.0
        assert created["energyActivationRatio"] == 1.0

        # Create another reserve with all properties set.
        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={
                "name": "Reserve Down 1",
                "type": "down",
                "failureCost": 10.0,
                "spillageCost": 20.0,
                "referenceActivationDuration": 5,
                "powerActivationRatio": 0.5,
                "energyActivationRatio": 0.8,
            },
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        created = res.json()
        assert created["id"] == "reserve down 1"
        assert created["failureCost"] == 10.0

        # Get the list of reserve definitions.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert {r["id"] for r in res.json()} == {"reserve up 1", "reserve down 1"}

        # Get a single reserve definition.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/reserve up 1")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json()["name"] == "Reserve Up 1"

        # Update a reserve definition (partial update).
        res = client.patch(
            f"/v1/studies/{study_id}/areas/fr/reserves/reserve up 1",
            json={"failureCost": 42.0},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        updated = res.json()
        assert updated["failureCost"] == 42.0
        assert updated["type"] == "up"  # unrelated fields untouched

        # Delete both reserve definitions at once.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json=["reserve up 1", "reserve down 1"],
        )
        assert res.status_code == http.HTTPStatus.NO_CONTENT, res.text

        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == []

    def test_create_reserve_definition_errors(self, client: TestClient, study_id: str) -> None:
        # Wrong area.
        res = client.post(
            f"/v1/studies/{study_id}/areas/fake_area/reserves",
            json={"name": "Reserve Up 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_area" in res.json()["description"]

        # Reserved reserve id.
        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"name": "Global Parameters", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        assert res.json()["exception"] == "ReservedReserveDefinitionId"

        # Duplicated reserve id.
        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"name": "Reserve Up 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        res = client.post(
            f"/v1/studies/{study_id}/areas/fr/reserves",
            json={"name": "Reserve Up 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "already exists" in res.json()["description"]

    def test_get_update_delete_reserve_definition_wrong_reserve(self, client: TestClient, study_id: str) -> None:
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/fake_reserve")
        assert res.status_code == http.HTTPStatus.NOT_FOUND, res.json()

        res = client.patch(
            f"/v1/studies/{study_id}/areas/fr/reserves/fake_reserve",
            json={"failureCost": 1.0},
        )
        assert res.status_code == http.HTTPStatus.NOT_FOUND, res.json()

    def test_reserve_definitions_wrong_study_version(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.post("/v1/studies", params={"name": "OldStudy", "version": 930})
        assert res.status_code in {200, 201}, res.json()
        old_study_id = res.json()

        res = client.post(f"/v1/studies/{old_study_id}/areas", json={"name": "FR", "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()

        res = client.post(
            f"/v1/studies/{old_study_id}/areas/fr/reserves",
            json={"name": "Reserve Up 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"


class TestThermalReserveSymmetriesAndCertifications:
    def test_symmetries_lifecycle(self, client: TestClient, study_id: str) -> None:
        for reserve_name in ["Reserve 1", "Reserve 2"]:
            res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": reserve_name, "type": "up"})
            assert res.status_code == http.HTTPStatus.OK, res.json()

        # No symmetries at first.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {}

        # A cluster can only be symmetric on reserves it is already certified for.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/thermals",
            json={
                "reserve 1": {"cluster 1": {}},
                "reserve 2": {"cluster 1": {}},
            },
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals",
            json={"cluster 1": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {"cluster 1": [["reserve 1", "reserve 2"]]}

        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {"cluster 1": [["reserve 1", "reserve 2"]]}

    def test_certifications_lifecycle(self, client: TestClient, study_id: str) -> None:
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 1", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()

        # No certifications at first.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/certifications/thermals")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {}

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/thermals",
            json={"reserve 1": {"cluster 1": {"participationCost": 10.0, "maxPower": 100.0}}},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        expected = {
            "reserve 1": {
                "cluster 1": {
                    "participationCost": 10.0,
                    "maxPower": 100.0,
                    "maxPowerOff": 0.0,
                    "participationCostOff": 0.0,
                }
            }
        }
        assert res.json() == expected

        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/certifications/thermals")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == expected

    def test_symmetries_wrong_reserve_and_cluster(self, client: TestClient, study_id: str) -> None:
        # Wrong reserve.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals",
            json={"cluster 1": [["fake_reserve", "other_reserve"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_reserve" in res.json()["description"]

        # Wrong cluster.
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 1", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 2", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals",
            json={"fake_cluster": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_cluster" in res.json()["description"]

    def test_symmetries_require_certifications(self, client: TestClient, study_id: str) -> None:
        for reserve_name in ["Reserve 1", "Reserve 2"]:
            res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": reserve_name, "type": "up"})
            assert res.status_code == http.HTTPStatus.OK, res.json()

        # A cluster declared symmetric on reserves it is not certified for should fail.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals",
            json={"cluster 1": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "ReserveCertificationNotFound" in res.json()["exception"] or "not found" in res.json()["description"]

    def test_certifications_wrong_study_version(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Certifications require v10.2, so a v10.0 study should be rejected.
        study_id = _create_study(client, user_access_token, "V10Study", "1000")

        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "FR", "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/thermals",
            json={"reserve 1": {"cluster 1": {}}},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"

        # Symmetries only require v10.0, so they should still be settable (though empty here).
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/thermals",
            json={},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()


class TestStStorageReserveSymmetriesAndCertifications:
    def test_symmetries_lifecycle(self, client: TestClient, study_id: str) -> None:
        for reserve_name in ["Reserve 1", "Reserve 2"]:
            res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": reserve_name, "type": "up"})
            assert res.status_code == http.HTTPStatus.OK, res.json()

        # No symmetries at first.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {}

        # A storage can only be symmetric on reserves it is already certified for.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/storages",
            json={
                "reserve 1": {"storage 1": {}},
                "reserve 2": {"storage 1": {}},
            },
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages",
            json={"storage 1": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {"storage 1": [["reserve 1", "reserve 2"]]}

        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {"storage 1": [["reserve 1", "reserve 2"]]}

    def test_certifications_lifecycle(self, client: TestClient, study_id: str) -> None:
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 1", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()

        # No certifications at first.
        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/certifications/storages")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {}

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/storages",
            json={"reserve 1": {"storage 1": {"participationCost": 5.0, "maxRelease": 50.0, "maxStore": 60.0}}},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        expected = {"reserve 1": {"storage 1": {"participationCost": 5.0, "maxRelease": 50.0, "maxStore": 60.0}}}
        assert res.json() == expected

        res = client.get(f"/v1/studies/{study_id}/areas/fr/reserves/certifications/storages")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == expected

    def test_symmetries_wrong_reserve_and_storage(self, client: TestClient, study_id: str) -> None:
        # Wrong reserve.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages",
            json={"storage 1": [["fake_reserve", "other_reserve"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_reserve" in res.json()["description"]

        # Wrong storage.
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 1", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()
        res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": "Reserve 2", "type": "up"})
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages",
            json={"fake_storage": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "fake_storage" in res.json()["description"]

    def test_symmetries_require_certifications(self, client: TestClient, study_id: str) -> None:
        for reserve_name in ["Reserve 1", "Reserve 2"]:
            res = client.post(f"/v1/studies/{study_id}/areas/fr/reserves", json={"name": reserve_name, "type": "up"})
            assert res.status_code == http.HTTPStatus.OK, res.json()

        # A storage declared symmetric on reserves it is not certified for should fail.
        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/symmetries/storages",
            json={"storage 1": [["reserve 1", "reserve 2"]]},
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, res.json()
        assert "not found" in res.json()["description"]

    def test_certifications_wrong_study_version(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Certifications require v10.2, so a v10.0 study should be rejected.
        study_id = _create_study(client, user_access_token, "V10Study", "1000")

        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "FR", "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"/v1/studies/{study_id}/areas/fr/reserves/certifications/storages",
            json={"reserve 1": {"storage 1": {}}},
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"


class TestReservesVariantStudy:
    def test_reserve_definitions_variant_lifecycle(self, client: TestClient, study_id: str) -> None:
        """The purpose of this test is to check that reserve definitions and symmetries/certifications
        can be managed from a variant study, and are correctly reflected once generated."""
        res = client.post(f"/v1/studies/{study_id}/variants", params={"name": "Variant 1"})
        assert res.status_code in {200, 201}, res.json()
        variant_id = res.json()

        res = client.post(
            f"/v1/studies/{variant_id}/areas/fr/reserves",
            json={"name": "Reserve 1", "type": "up"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.get(f"/v1/studies/{variant_id}/areas/fr/reserves")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert len(res.json()) == 1
        assert res.json()[0]["id"] == "reserve 1"
