# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from typing import List, Union
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.application import create_app_ctxt
from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTGroup, JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.launcher.main import build_launcher
from antarest.launcher.model import JobResult, JobResultDTO, JobStatus, LauncherParametersDTO, LogType

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def create_app(service: Mock) -> FastAPI:
    build_ctxt = create_app_ctxt(FastAPI(title=__name__))
    build_launcher(
        build_ctxt,
        output_service=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
        service_launcher=service,
        config=Config(security=SecurityConfig(disabled=True)),
        cache=Mock(),
    )
    return build_ctxt.build()


@pytest.mark.unit_test
def test_run() -> None:
    job = uuid4()
    study = "my-study"

    service = Mock()
    service.run_study.return_value = str(job)

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/run/{study}")

    assert res.status_code == 200
    assert res.json() == {"job_id": str(job)}
    service.run_study.assert_called_once_with(study, "local", LauncherParametersDTO(), RequestParameters(ADMIN), None)


@pytest.mark.unit_test
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
    service.get_result.assert_called_once_with(job, RequestParameters(DEFAULT_ADMIN_USER))


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
                RequestParameters(DEFAULT_ADMIN_USER),
                True,
                None,
            ),
            call(None, RequestParameters(DEFAULT_ADMIN_USER), True, None),
        ]
    )


@pytest.mark.unit_test
def test_get_solver_versions() -> None:
    service = Mock()
    output = ["1", "2", "3"]
    service.get_solver_versions.return_value = output

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/launcher/versions")
    res.raise_for_status()
    assert res.json() == output


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "solver, status_code, expected",
    [
        pytest.param(
            "",
            http.HTTPStatus.UNPROCESSABLE_ENTITY,
            "Input should be 'slurm', 'local' or 'default'",
            id="empty",
        ),
        pytest.param("default", http.HTTPStatus.OK, ["1", "2", "3"], id="default"),
        pytest.param("slurm", http.HTTPStatus.OK, ["1", "2", "3"], id="slurm"),
        pytest.param("local", http.HTTPStatus.OK, ["1", "2", "3"], id="local"),
        pytest.param(
            "remote",
            http.HTTPStatus.UNPROCESSABLE_ENTITY,
            "Input should be 'slurm', 'local' or 'default'",
            id="remote",
        ),
    ],
)
def test_get_solver_versions__with_query_string(
    solver: str,
    status_code: http.HTTPStatus,
    expected: Union[List[str], str],
) -> None:
    service = Mock()
    if status_code == http.HTTPStatus.OK:
        service.get_solver_versions.return_value = ["1", "2", "3"]
    else:
        service.get_solver_versions.side_effect = KeyError(solver)

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/versions?solver={solver}")
    assert res.status_code == status_code  # OK or UNPROCESSABLE_ENTITY
    if status_code == http.HTTPStatus.OK:
        assert res.json() == expected
    else:
        actual = res.json()["detail"][0]
        assert actual["type"] == "enum"
        assert actual["msg"] == expected


@pytest.mark.unit_test
def test_get_job_log() -> None:
    service = Mock()
    service.get_log.return_value = ""
    job_id = "job_id"

    app = create_app(service)
    client = TestClient(app)
    res = client.get(f"/v1/launcher/jobs/{job_id}/logs")
    assert res.status_code == 200
    service.get_log.assert_called_once_with(job_id, LogType.STDOUT, RequestParameters(user=DEFAULT_ADMIN_USER))


@pytest.mark.unit_test
def test_kill_job() -> None:
    service = Mock()
    service.kill_job.return_value.to_dto.return_value = ""
    job_id = "job_id"

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/jobs/{job_id}/kill")
    assert res.status_code == 200
    service.kill_job.assert_called_once_with(job_id=job_id, params=RequestParameters(user=DEFAULT_ADMIN_USER))
