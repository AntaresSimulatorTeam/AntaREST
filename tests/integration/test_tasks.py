# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.core.tasks.model import TaskDTO, TaskStatus
from tests.integration.utils import wait_task_completion


def test_list_tasks(client: TestClient, user_access_token: str, internal_study_id: str) -> None:
    client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

    # getting an internal study and doing multiple actions, so we can add tasks on it
    expected_task_list = []
    actual_task_list = []

    upgraded_internal_study = client.put(f"/v1/studies/{internal_study_id}/upgrade", params={"target_version": 860})
    task_id = upgraded_internal_study.json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED, task
    expected_task_list.append(task)

    copied_internal_study = client.post(f"/v1/studies/{internal_study_id}/copy?study_name=copied&use_task=true")
    task_id_2 = copied_internal_study.json()
    task_2 = wait_task_completion(client, user_access_token, task_id_2)
    assert task_2.status == TaskStatus.COMPLETED, task_2
    expected_task_list.append(task_2)

    res_tasks = client.get("/v1/tasks", params={})
    res_task_list = res_tasks.json()
    for task in res_task_list:
        task_dto = TaskDTO(**task)
        actual_task_list.append(task_dto)

    assert len(res_task_list) == 2
    assert actual_task_list == expected_task_list
