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

import pytest
from starlette.testclient import TestClient

from antarest.study.service import StudyService


@pytest.mark.parametrize("variant", [False, True])
def test_scenario_builder_nominal_case(variant: bool, study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "database"}
    ).json()
    if variant:
        study_id = client.post(f"/v1/studies/{study_id}/variants", params={"name": "variant_study"}).json()

    sc_builder_url = f"/v1/studies/{study_id}/gems/scenario-builder"

    # Ensures at first there is no sc-builder
    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {"scenarios": {}}

    # Set nbYears to 2 for the rest of the test
    res = client.put(f"/v1/studies/{study_id}/config/general/form", json={"nbYears": 2})
    assert res.status_code == 200

    # Add 2 scenarios, one with default values and the other ones with custom values
    res1 = client.post(sc_builder_url, params={"scenario_name": "scenario1"}, json=[])
    assert res1.status_code == 200
    assert res1.json() == [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 2}]

    res2 = client.post(
        sc_builder_url, params={"scenario_name": "scenario2"}, json=[{"scenario": 1, "timeSeriesIndex": 5}]
    )
    assert res2.status_code == 200
    assert res2.json() == [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 5}]

    # Fetch the 2 scenarios
    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {
        "scenarios": {
            "scenario1": [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 2}],
            "scenario2": [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 5}],
        }
    }

    # Update the data of 1 scenario only. The second one should not be impacted
    res = client.put(
        sc_builder_url, params={"scenario_name": "scenario1"}, json=[{"scenario": 0, "timeSeriesIndex": 3}]
    )
    assert res.status_code == 200
    assert res.json() == [{"scenario": 0, "timeSeriesIndex": 3}, {"scenario": 1, "timeSeriesIndex": 2}]

    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {
        "scenarios": {
            "scenario1": [{"scenario": 0, "timeSeriesIndex": 3}, {"scenario": 1, "timeSeriesIndex": 2}],
            "scenario2": [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 5}],
        }
    }

    # Delete the first scenario. The second one should not be impacted
    res = client.delete(sc_builder_url, params={"scenario_name": "scenario1"})
    assert res.status_code == 200

    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {
        "scenarios": {
            "scenario2": [{"scenario": 0, "timeSeriesIndex": 1}, {"scenario": 1, "timeSeriesIndex": 5}],
        }
    }

    # Delete the last scenario. Get response should be empty
    res = client.delete(sc_builder_url, params={"scenario_name": "scenario2"})
    assert res.status_code == 200

    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {"scenarios": {}}

    ##########################
    # Error cases
    ##########################

    # Try to update a fake scenario
    res = client.put(sc_builder_url, params={"scenario_name": "fake_scenario"}, json=[])
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Could not find scenario 'fake_scenario' inside gems scenario builder for study {study_id}",
        "exception": "GemsScenarioNotFound",
    }

    # Try to delete a fake scenario
    res = client.delete(sc_builder_url, params={"scenario_name": "fake_scenario"})
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Could not find scenario 'fake_scenario' inside gems scenario builder for study {study_id}",
        "exception": "GemsScenarioNotFound",
    }

    # Try to create a scenario with wrong years
    res = client.post(
        sc_builder_url, params={"scenario_name": "scenario1"}, json=[{"scenario": -1, "timeSeriesIndex": 1}]
    )
    assert res.status_code == 422
    assert res.json()["description"] == "Input should be greater than or equal to 0"
    assert res.json()["exception"] == "RequestValidationError"

    res = client.post(
        sc_builder_url, params={"scenario_name": "scenario1"}, json=[{"scenario": 1, "timeSeriesIndex": 0}]
    )
    assert res.status_code == 422
    assert res.json()["description"] == "Input should be greater than or equal to 1"
    assert res.json()["exception"] == "RequestValidationError"
