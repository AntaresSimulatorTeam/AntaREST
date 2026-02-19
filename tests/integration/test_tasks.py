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

    # Getting all COMPLETED tasks and ensuring there's 2 of them
    res_tasks = client.get("/v1/tasks?status=COMPLETED", params={})
    res_task_completed_list = res_tasks.json()
    assert len(res_task_completed_list) == 2
    for task_status in res_task_completed_list:
        assert task_status["status"] == TaskStatus.COMPLETED.value, task_status

    # Getting COMPLETED tasks, this time with his status value instead of a string
    res_tasks = client.get("/v1/tasks?status=3", params={})
    res_task_completed_list = res_tasks.json()
    assert len(res_task_completed_list) == 2

    # Getting all RUNNING tasks and making sure there's none
    res_tasks_running = client.get("/v1/tasks?status=RUNNING", params={}).json()
    assert len(res_tasks_running) == 0

    # Putting a non-existent status in the GET to have an error
    res_tasks_non_existent = client.get("/v1/tasks?status=NON_EXISTENT", params={})
    assert res_tasks_non_existent.status_code == 422, res_tasks_non_existent
