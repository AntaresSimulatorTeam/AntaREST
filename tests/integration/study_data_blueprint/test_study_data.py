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


from httpx import Headers
from starlette.testclient import TestClient

from antarest.core.serde.json import from_json
from antarest.core.tasks.model import TaskStatus
from tests.integration.study_data_blueprint import ASSETS_DIR
from tests.integration.utils import wait_task_completion


def test_study_data(client: TestClient, user_access_token: str, internal_study_id: str) -> None:
    client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

    # Upgrades the study in v9.3
    res = client.put(f"/v1/studies/{internal_study_id}/upgrade", params={"target_version": "9.3"})
    task_id = res.json()
    task = wait_task_completion(client, user_access_token, task_id, base_timeout=20)
    assert task.status == TaskStatus.COMPLETED

    # Add a binding constraint
    body = {"name": "Constraint1", "terms": [{"weight": 4, "data": {"area1": "de", "area2": "es"}}]}
    res = client.post(f"/v1/studies/{internal_study_id}/bindingconstraints", json=body)
    res.raise_for_status()

    # Change the enr-modeling to be able to create a renewable cluster
    body = {"renewableGenerationModelling": "clusters"}
    res = client.put(f"/v1/studies/{internal_study_id}/config/advancedparameters/form", json=body)
    res.raise_for_status()

    # Add a renewable inside area `fr`
    body = {
        "name": "solar cluster",
        "group": "Solar PV",
        "nominalCapacity": 5001,
        "unitCount": 1,
        "tsInterpretation": "production-factor",
        "enabled": True,
    }
    res = client.post(f"/v1/studies/{internal_study_id}/areas/fr/clusters/renewable", json=body)
    res.raise_for_status()

    # Add a short-term storage inside area `es`
    body = {"name": "my_battery", "group": "Battery"}
    res = client.post(f"/v1/studies/{internal_study_id}/areas/es/storages", json=body)
    res.raise_for_status()

    # Add a constraint inside the created sts
    body = [{"name": "C1?", "occurrences": [{"hours": [2, 3]}, {"hours": [148]}]}]
    res = client.post(f"/v1/studies/{internal_study_id}/areas/es/storages/my_battery/additional-constraints", json=body)
    res.raise_for_status()

    # todo: Once v10.2 is handled, add reserves in the test

    expected_result_path = ASSETS_DIR / "study_data.json"
    expected_json = from_json(expected_result_path.read_text())

    res = client.get(f"/v1/studies/{internal_study_id}/data")
    actual_json = res.json()

    # Sort the filters for areas to ensure test reproducibility
    for content in [actual_json, expected_json]:
        for area in content["areas"]:
            for key in ["filterByYear", "filterSynthesis"]:
                area["properties"][key] = sorted(area["properties"][key])

    assert actual_json == expected_json
