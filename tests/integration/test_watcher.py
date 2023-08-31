from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskResult


def test_scan_dir__no_path(app: FastAPI, admin_access_token: str) -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    res = client.post("/v1/watcher/_scan", headers=headers)
    assert res.status_code == 422
    assert res.json() == {
        "description": "field required",
        "exception": "RequestValidationError",
        "body": None,
    }


def test_scan_dir__default_workspace(
    app: FastAPI, admin_access_token: str
) -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    task_id = client.post(
        "/v1/watcher/_scan?path=/default",
        headers=headers,
    )
    # asserts that the POST request did not raise an Exception
    assert task_id.status_code == 200

    # asserts that the task failed
    res = client.get(
        f"v1/tasks/{task_id.json()}?wait_for_completion=true", headers=headers
    )
    task_result = TaskResult.parse_obj(res.json()["result"])
    assert not task_result.success
    assert (
        task_result.message
        == "Scan failed: You cannot scan the default internal workspace"
    )
    assert task_result.return_value is None


def test_scan_dir__unknown_folder(
    app: FastAPI, admin_access_token: str
) -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    fake_workspace_name = "fake_workspace"
    task_id = client.post(
        f"/v1/watcher/_scan?path={fake_workspace_name}",
        headers=headers,
    )

    # asserts that the POST request did not raise an Exception
    assert task_id.status_code == 200

    # asserts that the task failed
    res = client.get(
        f"v1/tasks/{task_id.json()}?wait_for_completion=true", headers=headers
    )
    task_result = TaskResult.parse_obj(res.json()["result"])
    assert not task_result.success
    assert (
        task_result.message
        == f"Task {task_id.json()} failed: Unhandled exception "
        f"(<HTTPStatus.BAD_REQUEST: 400>, 'Workspace {fake_workspace_name} not found')"
        f"\nSee the logs for detailed information and the error traceback."
    )
    assert task_result.return_value is None


def test_scan_dir__nominal_case(app: FastAPI, admin_access_token: str) -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    task_id = client.post(
        "/v1/watcher/_scan?path=ext",
        headers=headers,
    )

    # asserts that the POST request succeeded
    assert task_id.status_code == 200

    # asserts that the task succeeded
    res = client.get(
        f"v1/tasks/{task_id.json()}?wait_for_completion=true", headers=headers
    )
    task_result = TaskResult.parse_obj(res.json()["result"])
    assert task_result.success
    assert task_result.message == "Scan completed"
    assert task_result.return_value is None
