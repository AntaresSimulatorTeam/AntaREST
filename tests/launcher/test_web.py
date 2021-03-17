from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from flask import Flask

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import Event, EventType
from antarest.login.model import User
from antarest.common.requests import RequestParameters
from antarest.launcher.main import build_launcher
from antarest.launcher.model import JobResult, JobStatus


def create_app(service: Mock) -> Flask:
    app = Flask(__name__)

    build_launcher(
        app,
        service_launcher=service,
        config=Config({"security": {"disabled": True}}),
        db_session=Mock(),
    )
    return app


@pytest.mark.unit_test
def test_run() -> None:
    job = uuid4()
    study = "my-study"

    service = Mock()
    service.run_study.return_value = job

    app = create_app(service)
    client = app.test_client()
    res = client.post(f"/launcher/run/{study}")

    assert res.status_code == 200
    assert res.json == {"job_id": str(job)}
    service.run_study.assert_called_once_with(
        study, RequestParameters(User(id=0, name="admin", role="ADMIN"))
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
    client = app.test_client()
    res = client.get(f"/launcher/jobs/{job}")

    assert res.status_code == 200
    assert res.json == result.to_dict()
    service.get_result.assert_called_once_with(job)


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
    client = app.test_client()
    res = client.get(f"/launcher/jobs?study={str(study_id)}")
    assert res.status_code == 200
    assert res.json == [result.to_dict()]

    res = client.get(f"/launcher/jobs")
    assert res.status_code == 200
    assert res.json == [result.to_dict()]
    service.get_jobs.assert_has_calls([call(str(study_id)), call(None)])
