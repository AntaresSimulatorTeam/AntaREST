import contextlib
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


def wait_task_completion(
    client: TestClient,
    access_token: str,
    task_id: str,
    *,
    timeout: float = 10,
) -> TaskDTO:
    end_time = time.time() + timeout
    while time.time() < end_time:
        time.sleep(0.1)
        res = client.request(
            "GET",
            f"/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"wait_for_completion": True},
        )
        assert res.status_code == 200
        task = TaskDTO(**res.json())
        if task.status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
            return task
    raise TimeoutError(f"{timeout} seconds")
