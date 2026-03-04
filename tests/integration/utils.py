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

import contextlib
import logging
import os
import sys
import time
from typing import Callable

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus

logger = logging.getLogger(__name__)


def wait_for(predicate: Callable[[], bool], timeout: float = 10, sleep_time: float = 1) -> None:
    end = time.time() + timeout
    while time.time() < end:
        with contextlib.suppress(Exception):
            if predicate():
                return
        time.sleep(sleep_time)
    raise TimeoutError(f"task is still in progress after {timeout} seconds")


IS_WINDOWS = sys.platform == "win32"


def is_windows_ci() -> bool:
    """
    Check if running on Windows in GitHub Actions CI.
    """
    return IS_WINDOWS and os.getenv("GITHUB_ACTIONS") == "true"


def duration_threshold(base_duration: float) -> float:
    """
    base_duration is multiplied by 2 on Windows CI to cope with slow CI runners
    """
    multiplier = 2 if is_windows_ci() else 1
    return multiplier * base_duration


def wait_task_completion(
    client: TestClient,
    access_token: str | None,
    task_id: str,
    *,
    base_timeout: float = 10,
) -> TaskDTO:
    """
    base_timeout is multiplied by 2 on Windows CI to cope with slow CI runners
    """
    timeout = duration_threshold(base_timeout)
    params = {"wait_for_completion": True, "timeout": timeout}
    res = client.request(
        "GET",
        f"/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {access_token}"} if access_token else {},
        params=params,
    )
    if res.status_code == 200:
        task = TaskDTO(**res.json())
        if task.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            return task
    elif res.status_code == 408:
        raise TimeoutError(f"{timeout} seconds")
    raise ValueError(f"Unexpected status code {res.status_code}")
