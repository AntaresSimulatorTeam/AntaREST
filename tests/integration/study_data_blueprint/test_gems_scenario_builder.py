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
    print(res1.json())
    print("//////")
    scenario2 = client.post(
        sc_builder_url, params={"scenario_name": "scenario2"}, json=[{"scenario": 1, "timeSeriesIndex": 5}]
    ).json()
    print(scenario2)
