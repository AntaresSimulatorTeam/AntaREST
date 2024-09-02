# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest import __version__
from antarest.core.config import Config, SecurityConfig, StorageConfig, WorkspaceConfig
from antarest.core.core_blueprint import create_utils_routes
from antarest.study.model import DEFAULT_WORKSPACE_NAME

CONFIG = Config(
    resources_path=Path(),
    security=SecurityConfig(disabled=True),
    storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=Path())}),
)


@pytest.mark.unit_test
def test_version() -> None:
    mock_storage_service = Mock()
    mock_storage_service.study_service.path_resources = Path("/")

    app = FastAPI(title=__name__)
    app.include_router(create_utils_routes(Config()))
    client = TestClient(app)

    path = "/version"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert result.json()["version"] == __version__


@pytest.mark.unit_test
def test_server_health() -> None:
    app = FastAPI(title=__name__)
    app.include_router(create_utils_routes(Config()))
    client = TestClient(app)
    result = client.get("/health")
    assert result.json() == {"status": "available"}
