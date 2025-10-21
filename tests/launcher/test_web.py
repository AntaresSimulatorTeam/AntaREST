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
from antarest.core.jwt import JWTGroup, JWTUser
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
        study_service=Mock(),
        output_service=Mock(),
        login_service=Mock(),
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
    service.run_study.assert_called_once_with(study, "local", LauncherParametersDTO(), None, None)


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
        pytest.param("default", http.HTTPStatus.OK, ["1", "2", "3"], id="default"),
        pytest.param("slurm", http.HTTPStatus.OK, ["1", "2", "3"], id="slurm"),
        pytest.param("local", http.HTTPStatus.OK, ["1", "2", "3"], id="local"),
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
    service.get_log.assert_called_once_with(job_id, LogType.STDOUT)


@pytest.mark.unit_test
def test_kill_job() -> None:
    service = Mock()
    service.kill_job.return_value.to_dto.return_value = ""
    job_id = "job_id"

    app = create_app(service)
    client = TestClient(app)
    res = client.post(f"/v1/launcher/jobs/{job_id}/kill")
    assert res.status_code == 200
    service.kill_job.assert_called_once_with(job_id=job_id)


def test_create_launcher_config() -> None:
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    """Test creating a new launcher configuration"""
    payload = {
        "name": "testxpressconfig",
        "linear_solver": "xpress",
        "min_antares_version": {"major": 9, "minor": 2, "patch": 0},
        "linear_solver_param_optim_1": [["THREADS", "4"], ["PRESOLVE", "1"]],
        "linear_solver_param_optim_2": [["MIPRELSTOP", "0.01"]],
        "linear_solver_param": [["DEFAULTALG", "4"]],
        "use_optim_1_basis_next_week": True,
        "use_optim_1_basis_optim_2": False,
    }

    res = client.post(
        "/v1/launcher/configurations",
        json=payload,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "test-xpress-config"
    assert data["linear_solver"] == "xpress"
    assert "id" in data
    assert data["min_antares_version"] == "9.2.0"
    assert data["use_optim_1_basis_optim_2"] is False


def test_create_launcher_config_minimal() -> None:
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    """Test creating a launcher config with minimal required fields"""
    payload = {
        "name": "minimal-config",
        "linear_solver": "sirius",
    }

    res = client.post(
        "/v1/launcher/configurations",
        json=payload,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "minimal-config"
    assert data["linear_solver"] == "sirius"
    assert data["use_optim_1_basis_next_week"] is True
    assert data["use_optim_1_basis_optim_2"] is True


def test_get_launcher_config() -> None:
    """Test retrieving a launcher configuration by ID"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    # First create a config
    create_payload = {
        "name": "retrieve-test",
        "linear_solver": "coin",
        "min_antares_version": "8.0.0",
        "linear_solver_param": [["THREADS", "2"]],
    }

    create_res = client.post(
        "/v1/launcher/configurations",
        json=create_payload,
    )
    config_id = create_res.json()["id"]

    # Now retrieve it
    res = client.get(
        f"/v1/launcher/configurations/{config_id}",
    )

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == config_id
    assert data["name"] == "retrieve-test"
    assert data["linear_solver"] == "coin"
    assert data["linear_solver_param"] == [["THREADS", "2"]]


def test_get_launcher_config_not_found() -> None:
    """Test retrieving a non-existent launcher configuration"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    res = client.get(
        "/v1/launcher/configurations/nonexistent-id",
    )

    assert res.status_code == 404


def test_get_all_launcher_configs() -> None:
    """Test retrieving all launcher configurations"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    # Create multiple configs
    configs = [
        {"name": "config-1", "linear_solver": "coin"},
        {"name": "config-2", "linear_solver": "xpress", "min_antares_version": "9.2.0"},
    ]

    for config in configs:
        client.post(
            "/v1/launcher/configurations",
            json=config,
        )

    # Retrieve all configs
    res = client.get(
        "/v1/launcher/configurations/",
    )

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    config_names = [c["name"] for c in data]
    assert "config-1" in config_names
    assert "config-2" in config_names


def test_update_launcher_config() -> None:
    """Test updating an existing launcher configuration"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    # Create initial config
    create_payload = {
        "name": "update-test",
        "linear_solver": "xpress",
        "linear_solver_param": [["THREADS", "4"]],
    }

    create_res = client.post(
        "/v1/launcher/configurations",
        json=create_payload,
    )
    config_id = create_res.json()["id"]

    # Update the config
    update_payload = {
        "name": "updated-config",
        "linear_solver": "xpress",
        "min_antares_version": "9.2.0",
        "linear_solver_param_optim_1": [["PRESOLVE", "2"]],
        "linear_solver_param": [["THREADS", "8"]],
        "use_optim_1_basis_next_week": False,
    }

    res = client.put(
        f"/v1/launcher/configurations/{config_id}",
        json=update_payload,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == config_id
    assert data["name"] == "updated-config"
    assert data["linear_solver_param"] == [["THREADS", "8"]]
    assert data["linear_solver_param_optim_1"] == [["PRESOLVE", "2"]]
    assert data["use_optim_1_basis_next_week"] is False


def test_update_launcher_config_not_found() -> None:
    """Test updating a non-existent launcher configuration"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    update_payload = {
        "name": "nonexistent",
        "linear_solver": "coin",
    }

    res = client.put(
        "/v1/launcher/configurations/nonexistent-id",
        json=update_payload,
    )

    assert res.status_code == 404


def test_create_launcher_config_invalid_empty_name() -> None:
    """Test creating a launcher config with empty name"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    invalid_payload = {
        "name": "   ",  # Empty/whitespace name
        "linear_solver": "xpress",
    }

    res = client.post(
        "/v1/launcher/configurations",
        json=invalid_payload,
    )

    assert res.status_code == 422


def test_create_launcher_config_invalid_version_range() -> None:
    """Test creating a launcher config with min > max version"""
    service = Mock()
    app = create_app(service)
    client = TestClient(app)

    invalid_payload = {
        "name": "invalid-version-range",
        "linear_solver": "xpress",
        "min_antares_version": "10.0.0",
        "max_antares_version": "9.0.0",  # max < min
    }

    res = client.post(
        "/v1/launcher/configurations",
        json=invalid_payload,
    )

    assert res.status_code == 422
