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

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import numpy as np
import polars as pl
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.config import Config, SecurityConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import JwtSettings
from antarest.main import add_exception_handlers
from antarest.matrixstore.model import MatrixDescriptionDTO, MatrixInfoDTO, MatrixReference, MatrixReferencesDTO
from antarest.matrixstore.web import MatrixDTO, create_matrix_api
from tests.helpers import with_admin_user
from tests.login.test_web import create_auth_token


def create_app(service: Mock, auth_disabled: bool = False) -> FastAPI:
    config = Config(
        resources_path=Path(),
        security=SecurityConfig(disabled=auth_disabled),
    )

    @AuthJWT.load_config  # type: ignore[misc]
    def get_config() -> JwtSettings:
        return JwtSettings(
            authjwt_secret_key="super-secret",
            authjwt_token_location=("headers", "cookies"),
            authjwt_denylist_enabled=False,
        )

    app = FastAPI(title=__name__)
    add_exception_handlers(app)
    app.state.config = config
    app.state.matrix_service = service
    app.state.file_transfer_manager = Mock()
    app.state.task_service = Mock()
    app.state.login_service = Mock()
    app.include_router(create_matrix_api())
    return app


@with_admin_user
def test_create() -> None:
    service = Mock()
    service.create.return_value = "matrix_hash"

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/matrix",
        headers=create_auth_token(app),
        json=[[1]],
    )
    assert res.status_code == 200
    assert res.json() == "matrix_hash"


@with_admin_user
def test_get() -> None:
    matrix = MatrixDTO(
        id="123",
        width=2,
        height=2,
        created_at=0,
        index=[0, 1],
        columns=["a", "b"],
        data=[[1, 2], [3, 4]],
    )

    service = Mock()
    service.get.return_value = pl.DataFrame(data=np.array([[1, 2], [3, 4]]), schema=["a", "b"])

    app = create_app(service)
    client = TestClient(app)
    res = client.get("/v1/matrix/123", headers=create_auth_token(app))
    assert res.status_code == 200
    assert res.json() == matrix.model_dump()
    service.get.assert_called_once_with("123")


def test_delete() -> None:
    id = "123"
    service = Mock()
    service.delete.return_value = id

    app = create_app(service)
    client = TestClient(app)
    res = client.delete("/v1/matrixdataset/123", headers=create_auth_token(app))
    assert res.status_code == 200


@with_admin_user
def test_import() -> None:
    matrix_info = [MatrixInfoDTO(id="123", name="Matrix/matrix.txt")]
    service = Mock()
    service.create_by_importation.return_value = matrix_info

    app = create_app(service)
    client = TestClient(app)
    res = client.post(
        "/v1/matrix/_import",
        headers=create_auth_token(app),
        files={"file": ("Matrix.zip", bytes(5), "application/zip")},
    )
    assert res.status_code == 200
    assert [MatrixInfoDTO.model_validate(res.json()[0])] == matrix_info


@with_admin_user
def test_get_matrices_references() -> None:
    command_id = "a68de4b5e96a60c8ceb3c7b7ef93461725bdbbff3516b136585a743b5c0ec664"
    dataset_id = "data_1"
    study_id = "study_id"
    ref_one = MatrixDescriptionDTO(description=f"Referenced by command {command_id} of study study1")
    ref_two = MatrixDescriptionDTO(description=f"Referenced by raw study {study_id}")
    ref_three = MatrixDescriptionDTO(description="Constant matrix")
    ref_four = MatrixDescriptionDTO(description=f"Referenced by dataset {dataset_id}")
    refs_one = [ref_one, ref_two]
    refs_two = [ref_three]
    refs_three = [ref_four]

    disk_usage = 24
    matrix_reference_one = MatrixReferencesDTO(refs=refs_one, disk_usage=disk_usage)
    matrix_reference_two = MatrixReferencesDTO(refs=refs_two, disk_usage=disk_usage)
    matrix_reference_three = MatrixReferencesDTO(refs=refs_three, disk_usage=disk_usage)
    matrix_dict = {
        command_id: matrix_reference_one,
        "constant_id_1": matrix_reference_two,
        "test": matrix_reference_three,
    }
    service = Mock()
    matrix_references = {
        MatrixReference(matrix_id=command_id, use_description=f"Referenced by command {command_id} of study study1"),
        MatrixReference(matrix_id=command_id, use_description=f"Referenced by raw study {study_id}"),
        MatrixReference(matrix_id="constant_id_1", use_description="Constant matrix"),
        MatrixReference(matrix_id="test", use_description=f"Referenced by dataset {dataset_id}"),
    }
    service.get_used_matrices.return_value = matrix_references

    service.get_matrices_references.return_value = matrix_dict
    app = create_app(service)
    client = TestClient(app)
    user = DEFAULT_ADMIN_USER
    res = client.get(
        "/v1/matrix/_references/", headers=create_auth_token(app=app, user=user), params={"disk_usage": True}
    )

    res_dict_test = creating_json_res_dict(res)

    sorted_matrix_dict = dict(sorted(matrix_dict.items()))
    sorted_res_matrix_dict = dict(sorted(res_dict_test.items()))
    assert res.status_code == 200
    assert sorted_res_matrix_dict == sorted_matrix_dict

    matrix_reference_one = MatrixReferencesDTO(refs=refs_one, disk_usage=None)
    matrix_reference_two = MatrixReferencesDTO(refs=refs_two, disk_usage=None)
    matrix_reference_three = MatrixReferencesDTO(refs=refs_three, disk_usage=None)
    matrix_dict = {
        command_id: matrix_reference_one,
        "constant_id_1": matrix_reference_two,
        "test": matrix_reference_three,
    }

    service.get_used_matrices.return_value = matrix_references

    service.get_matrices_references.return_value = matrix_dict

    res = client.get(
        "/v1/matrix/_references/", headers=create_auth_token(app=app, user=user), params={"disk_usage": False}
    )
    assert res.status_code == 200
    data__ = {
        f"{command_id}": {
            "refs": [
                {"description": f"Referenced by command {command_id} of study study1"},
                {"description": "Referenced by raw study study_id"},
            ]
        },
        "constant_id_1": {"refs": [{"description": "Constant matrix"}]},
        "test": {"refs": [{"description": "Referenced by dataset data_1"}]},
    }
    assert res.json() == data__


def creating_json_res_dict(res: Any) -> dict[str, MatrixReferencesDTO]:
    res_dict_test = {}
    for matrix_id in res.json():
        description = res.json()[matrix_id]["refs"]
        disk_usage = None
        if "disk_usage" in res.json()[matrix_id]:
            disk_usage = res.json()[matrix_id]["disk_usage"]
        descs_dto = sorted(
            [MatrixDescriptionDTO(description=desc["description"]) for desc in description],
            key=lambda x: x.description,
            reverse=False,
        )
        refs_dto = MatrixReferencesDTO(refs=descs_dto, disk_usage=disk_usage)
        res_dict_test.update({matrix_id: refs_dto})

    return res_dict_test
