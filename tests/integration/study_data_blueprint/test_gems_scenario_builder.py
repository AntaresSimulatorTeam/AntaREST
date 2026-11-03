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

    # Ensures at first there is no sc-builder
    sc_builder_url = f"/v1/studies/{study_id}/gems/scenario-builder"
    res = client.get(sc_builder_url)
    assert res.status_code == 200
    assert res.json() == {"scenarios": {}}
