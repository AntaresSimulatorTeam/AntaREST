from unittest.mock import Mock
from uuid import uuid4

import pytest
from flask import Flask

from antarest.common.config import Config
from antarest.launcher.main import build_launcher
from antarest.launcher.model import JobResult, JobStatus


def create_app(service: Mock) -> Flask:

    app = Flask(__name__)

    build_launcher(
        app,
        service_launcher=service,
        config=Config({}),
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
    service.run_study.assert_called_once_with(study)


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
