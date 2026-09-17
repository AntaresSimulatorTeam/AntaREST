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


def test_get_scenario_builder_for_study_with_binding_constraint_without_group(admin_client: TestClient):
    # For studies which versionis <= 8.6, binding constraints do not have a group.
    # This test makes sure that the scenario builder is still accessible for such studies.
    res = admin_client.post("/v1/studies", params={"name": "study-for-auth-test", "version": "8.6"})
    assert res.status_code == 201, res.json()
    study_id = res.json()

    res = admin_client.post(f"/v1/studies/{study_id}/bindingconstraints", json={"name": "bc_1"})
    assert res.status_code == 200, res.json()

    res = admin_client.get(f"/v1/studies/{study_id}/config/scenariobuilder/load")
    assert res.status_code == 200, res.json()
