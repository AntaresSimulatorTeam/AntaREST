import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient


@pytest.fixture(name="client")
def fixture_client(app: FastAPI) -> TestClient:
    """Get the webservice client used for unit testing"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(name="admin_access_token")
def fixture_admin_access_token(client: TestClient) -> str:
    """Get the admin user access token used for authentication"""
    res = client.post(
        "/v1/login",
        json={"username": "admin", "password": "admin"},
    )
    assert res.status_code == 200
    credentials = res.json()
    return credentials["access_token"]


@pytest.fixture(name="user_access_token")
def fixture_user_access_token(
    client: TestClient,
    admin_access_token: str,
) -> str:
    """Get a classic user access token used for authentication"""
    res = client.post(
        "/v1/users",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={"name": "George", "password": "mypass"},
    )
    assert res.status_code == 200
    res = client.post(
        "/v1/login",
        json={"username": "George", "password": "mypass"},
    )
    assert res.status_code == 200
    credentials = res.json()
    return credentials["access_token"]


@pytest.fixture(name="study_id")
def fixture_study_id(
    client: TestClient,
    user_access_token: str,
) -> str:
    """Get the ID of the study to upgrade"""
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )
    assert res.status_code == 200
    study_ids = res.json()
    return next(iter(study_ids))
