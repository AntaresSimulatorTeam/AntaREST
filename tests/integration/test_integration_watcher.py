from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus


def test_integration_watcher(app: FastAPI, tmp_path: str):
    client = TestClient(app)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    headers = {"Authorization": f'Bearer {admin_credentials["access_token"]}'}

    res = client.post("/v1/watcher/_scan", headers=headers)
    assert res.status_code == 422
    assert res.json() == {
        "description": "field required",
        "exception": "RequestValidationError",
        "body": None,
    }

    task_id = client.post(
        "/v1/watcher/_scan?path=/default",
        headers=headers,
    ).json()

    # asserts that scanning default workspace doesn't fail
    res = client.get(
        f"v1/tasks/{task_id}?wait_for_completion=true", headers=headers
    ).json()
    assert res["status"] == TaskStatus.COMPLETED.value
