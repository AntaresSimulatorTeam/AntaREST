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

import http
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.roles import RoleType
from antarest.launcher.model import JobResult, JobResultDTO, JobStatus, LauncherParametersDTO, LogType
from antarest.launcher.web import create_launcher_api
from antarest.main import add_exception_handlers
from tests.dishka_utils import setup_test_dishka

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def create_app(service: Mock) -> FastAPI:
    config = Config(security=SecurityConfig(disabled=True))
    services = Mock()
    services.launcher = service
    app = FastAPI(title=__name__)
    add_exception_handlers(app)
    app.include_router(create_launcher_api())
    setup_test_dishka(app, config, services)
    return app


def test_run() -> None:
    job = uuid4()
    study = str(uuid4())

    service = Mock()
    service.run_study.return_value = str(job)

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/run/{study}")

    assert res.status_code == 200
    assert res.json() == {"job_id": str(job)}
    service.run_study.assert_called_once_with(study, "local", LauncherParametersDTO(), None, None)


def test_result() -> None:
    job = uuid4()
    result = JobResult(
        id=str(job),
        study_id=str(uuid4()),
        job_status=JobStatus.SUCCESS,
        msg="hello world",
        exit_code=0,
        owner_id=1,
    )

    service = Mock()
    service.get_result.return_value = result

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs/{job}")

    assert res.status_code == 200
    assert JobResultDTO.model_validate(res.json()) == result.to_dto()
    service.get_result.assert_called_once_with(job)


def test_jobs() -> None:
    job_id = uuid4()
    study_id = uuid4()
    result = JobResult(
        id=str(job_id),
        study_id=str(study_id),
        job_status=JobStatus.SUCCESS,
        msg="hello world",
        exit_code=0,
        owner_id=1,
    )

    service = Mock()
    service.get_jobs.return_value = [result]

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs?study={str(study_id)}")
    assert res.status_code == 200
    assert [JobResultDTO.model_validate(j) for j in res.json()] == [result.to_dto()]

    res = client.get("/v1/launcher/jobs")
    assert res.status_code == 200
    assert [JobResultDTO.model_validate(j) for j in res.json()] == [result.to_dto()]
    service.get_jobs.assert_has_calls(
        [
            call(
                str(study_id),
                True,
                None,
            ),
            call(None, True, None),
        ]
    )


def test_get_solver_versions() -> None:
    service = Mock()
    output = ["1", "2", "3"]
    service.get_solver_versions.return_value = output

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/launcher/versions")
    res.raise_for_status()
    assert res.json() == output


@pytest.mark.parametrize(
    "launcher",
    [
        "default",
        "slurm",
        "local",
    ],
)
@pytest.mark.parametrize(
    "param_name",
    [
        "solver",  # deprecated
        "launcher_id",
    ],
)
def test_get_solver_versions__with_query_string(
    launcher: str,
    param_name: str,
) -> None:
    service = Mock()
    service.get_solver_versions.return_value = ["1", "2", "3"]

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/versions?{param_name}={launcher}")
    assert res.status_code == http.HTTPStatus.OK  # OK or UNPROCESSABLE_ENTITY
    assert res.json() == ["1", "2", "3"]


def test_get_job_log() -> None:
    service = Mock()
    service.get_log.return_value = ""
    job_id = "job_id"

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs/{job_id}/logs")
    assert res.status_code == 200
    service.get_log.assert_called_once_with(job_id, LogType.STDOUT)


def test_kill_job() -> None:
    service = Mock()
    service.kill_job.return_value.to_dto.return_value = JobResultDTO(
        id="job_id",
        study_id="study",
        output_id="output",
        exit_code=10,
        launcher=None,
        launcher_params=None,
        msg=None,
        owner=None,
        status=JobStatus.SUCCESS,
        solver_stats=None,
        creation_date="date",
        completion_date=None,
    )
    job_id = "job_id"

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/jobs/{job_id}/kill")
    assert res.status_code == 200
    service.kill_job.assert_called_once_with(job_id=job_id)
