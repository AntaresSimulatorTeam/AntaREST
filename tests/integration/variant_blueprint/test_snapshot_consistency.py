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


def test_parent_modification_triggers_update(admin_client: TestClient) -> None:
    client = admin_client

    # Create a Variant study
    res = client.post("/v1/studies?name=RawStudy")
    assert res.status_code == 201
    study_id = res.json()

    res = client.post(f"/v1/studies/{study_id}/variants?name=variant1")
    assert res.status_code == 200
    variant1_id = res.json()

    res = client.post(f"/v1/studies/{variant1_id}/variants?name=variant2")
    assert res.status_code == 200
    variant2_id = res.json()

    # Create an area in child study
    res = client.post(f"/v1/studies/{variant2_id}/areas", json={"name": "area1"})
    assert res.status_code == 200

    # Assert we can retrieve the area successfully
    res = client.get(f"/v1/studies/{variant2_id}/areas")
    assert res.status_code == 200
    assert set(area["id"] for area in res.json()) == {"area1"}

    # Adds an area to the root study. Should trigger invalidation of the children snapshots
    res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "area2"})
    assert res.status_code == 200

    # Assert we now retrieve both areas in the variant study
    res = client.get(f"/v1/studies/{variant2_id}/areas")
    assert res.status_code == 200
    assert set(area["id"] for area in res.json()) == {"area1", "area2"}

    # Adds an area to the intermediate variant study.
    res = client.post(f"/v1/studies/{variant1_id}/areas", json={"name": "area3"})
    assert res.status_code == 200

    # Assert we now retrieve the new area in the child study, identified as not up to date
    res = client.get(f"/v1/studies/{variant2_id}/areas")
    assert res.status_code == 200
    assert set(area["id"] for area in res.json()) == {"area1", "area2", "area3"}
