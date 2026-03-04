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


from integration.study_data_blueprint import ASSETS_DIR
from integration.utils import wait_task_completion
from starlette.testclient import TestClient

from antarest.core.serde.json import from_json
from antarest.core.tasks.model import TaskStatus


def test_study_data(client: TestClient, user_access_token: str, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Upgrades the study in v8.8
    res = client.put(f"/v1/studies/{internal_study_id}/upgrade", params={"target_version": "8.8"})
    task_id = res.json()
    task = wait_task_completion(client, user_access_token, task_id, base_timeout=20)
    assert task.status == TaskStatus.COMPLETED

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
