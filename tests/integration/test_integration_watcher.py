from fastapi import FastAPI
from starlette.testclient import TestClient


def test_integration_xpansion(app: FastAPI, tmp_path: str):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    headers = {"Authorization": f'Bearer {admin_credentials["access_token"]}'}

    client.post(
        f"/v1/watcher/_scan",
        headers=headers,
    )
    client.post(
        f"/v1/watcher/_scan?path=/tmp",
        headers=headers,
    )
