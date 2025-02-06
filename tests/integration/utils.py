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

import contextlib
import os
import time
from typing import Callable

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus


def wait_for(predicate: Callable[[], bool], timeout: float = 10, sleep_time: float = 1) -> None:
    end = time.time() + timeout
    while time.time() < end:
        with contextlib.suppress(Exception):
            if predicate():
                return
        time.sleep(sleep_time)
    raise TimeoutError(f"task is still in progress after {timeout} seconds")


IS_WINDOWS = os.name == "nt"
TIMEOUT_MULTIPLIER = 2 if IS_WINDOWS else 1


def wait_task_completion(
    client: TestClient,
    access_token: str,
    task_id: str,
    *,
    base_timeout: float = 10,
) -> TaskDTO:
    """
    base_timeout is multiplied by 2 on windows to cope with slow CI
    """
    timeout = TIMEOUT_MULTIPLIER * base_timeout
    params = {"wait_for_completion": True, "timeout": timeout}
    res = client.request(
        "GET",
        f"/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    if res.status_code == 200:
        task = TaskDTO(**res.json())
        if task.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            return task
    elif res.status_code == 408:
        raise TimeoutError(f"{timeout} seconds")
    raise ValueError(f"Unexpected status code {res.status_code}")
