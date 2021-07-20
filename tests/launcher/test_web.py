from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import JWTUser, JWTGroup, DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.launcher.main import build_launcher
from antarest.launcher.model import JobResult, JobStatus

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def create_app(service: Mock) -> FastAPI:
    app = FastAPI(title=__name__)

    build_launcher(
        app,
        service_launcher=service,
        config=Config(security=SecurityConfig(disabled=True)),
    )
    return app


@pytest.mark.unit_test
def test_run() -> None:
    job = uuid4()
    study = "my-study"

    service = Mock()
    service.run_study.return_value = job

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/run/{study}")

    assert res.status_code == 200
    assert res.json() == {"job_id": str(job)}
    service.run_study.assert_called_once_with(
        study, RequestParameters(ADMIN), "local"
    )


@pytest.mark.unit_test
def test_result() -> None:
    job = uuid4()
    result = JobResult(
        id=str(job),
        job_status=JobStatus.SUCCESS,
        msg="hello world",
        exit_code=0,
    )

    service = Mock()
    service.get_result.return_value = result

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs/{job}")

    assert res.status_code == 200
    assert res.json() == result.to_dict()
    service.get_result.assert_called_once_with(
        job, RequestParameters(DEFAULT_ADMIN_USER)
    )


@pytest.mark.unit_test
def test_jobs() -> None:
    job_id = uuid4()
    study_id = uuid4()
    result = JobResult(
        id=str(job_id),
        study_id=str(study_id),
        job_status=JobStatus.SUCCESS,
        msg="hello world",
        exit_code=0,
    )

    service = Mock()
    service.get_jobs.return_value = [result]

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs?study={str(study_id)}")
    assert res.status_code == 200
    assert res.json() == [result.to_dict()]

    res = client.get(f"/v1/launcher/jobs")
    assert res.status_code == 200
    assert res.json() == [result.to_dict()]
    service.get_jobs.assert_has_calls(
        [
            call(str(study_id), RequestParameters(DEFAULT_ADMIN_USER)),
            call(None, RequestParameters(DEFAULT_ADMIN_USER)),
        ]
    )
