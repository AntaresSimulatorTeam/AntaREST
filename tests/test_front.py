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

from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.front import RedirectMiddleware, add_front_app


@pytest.fixture
def base_back_app() -> FastAPI:
    """
    A simple app which has only one backend endpoint
    """
    app = FastAPI(title=__name__)

    @app.get(path="/api/a-backend-endpoint")
    def get_from_api() -> str:
        return "back"

    return app


@pytest.fixture
def resources_dir(tmp_path: Path) -> Path:
    resource_dir = tmp_path / "resources"
    resource_dir.mkdir()
    webapp_dir = resource_dir / "webapp"
    webapp_dir.mkdir()
    with open(webapp_dir / "index.html", mode="w") as f:
        f.write("index")
    with open(webapp_dir / "front.css", mode="w") as f:
        f.write("css")
    return resource_dir


@pytest.fixture
def app_with_home(base_back_app) -> FastAPI:
    """
    A simple app which has only a home endpoint and one backend endpoint
    """

    @base_back_app.get(path="/")
    def home() -> str:
        return "home"

    return base_back_app


@pytest.fixture
def redirect_app(app_with_home: FastAPI) -> FastAPI:
    """
    Same as app with redirect middleware
    """
    app_with_home.add_middleware(
        RedirectMiddleware, protected_roots=["/api", "static"], protected_paths=["/config.json"]
    )
    return app_with_home


def test_redirect_middleware_does_not_modify_home(redirect_app: FastAPI) -> None:
    client = TestClient(redirect_app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "home"


def test_redirect_middleware_redirects_unknown_routes_to_home(redirect_app: FastAPI) -> None:
    client = TestClient(redirect_app)
    response = client.get("/a-front-route")
    assert response.status_code == 200
    assert response.json() == "home"


def test_redirect_middleware_does_not_redirect_backend_routes(redirect_app: FastAPI) -> None:
    client = TestClient(redirect_app)
    response = client.get("/api/a-backend-endpoint")
    assert response.status_code == 200
    assert response.json() == "back"


def test_frontend_paths(base_back_app, resources_dir: Path) -> None:
    add_front_app(base_back_app, resources_dir, "/api")
    client = TestClient(base_back_app)

    config_response = client.get("/config.json")
    assert config_response.status_code == 200
    assert config_response.json() == {"restEndpoint": "/api", "wsEndpoint": "/api/ws"}

    index_response = client.get("/index.html")
    assert index_response.status_code == 200
    assert index_response.text == "index"

    front_route_response = client.get("/any-route")
    assert front_route_response.status_code == 200
    assert front_route_response.text == "index"

    front_route_response = client.get("/apidoc")
    assert front_route_response.status_code == 200
    assert front_route_response.text == "index"

    front_static_file_response = client.get("/static/front.css")
    assert front_static_file_response.status_code == 200
    assert front_static_file_response.text == "css"
