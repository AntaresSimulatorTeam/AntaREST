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

import os
import typing as t
import zipfile
from pathlib import Path

import jinja2
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine  # type: ignore
from starlette.testclient import TestClient

from antarest.dbmodel import Base
from antarest.main import fastapi_app
from tests.integration.assets import ASSETS_DIR

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")

RUN_ON_WINDOWS = os.name == "nt"


@pytest.fixture(name="app")
def app_fixture(tmp_path: Path) -> t.Generator[FastAPI, None, None]:
    # Currently, it is impossible to use a SQLite database in memory (with "sqlite:///:memory:")
    # because the database is created by the FastAPI application during each integration test,
    # which doesn't apply the migrations (migrations are done by Alembic).
    # An alternative is to use a SQLite database stored on disk, because migrations can be persisted.
    db_path = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_path}"

    # ATTENTION: when setting up integration tests, be aware that creating the database
    # tables requires a dedicated DB engine (the `engine` below).
    # This is crucial as the FastAPI application initializes its own engine (a global object),
    # and the DB engine used in integration tests is not the same.
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    del engine  # This object won't be used anymore.

    # Prepare the directories used by the repos
    matrix_dir = tmp_path / "matrix_store"
    archive_dir = tmp_path / "archive_dir"
    tmp_dir = tmp_path / "tmp"
    default_workspace = tmp_path / "internal_workspace"
    ext_workspace_path = tmp_path / "ext_workspace"

    matrix_dir.mkdir()
    archive_dir.mkdir()
    tmp_dir.mkdir()
    default_workspace.mkdir()
    ext_workspace_path.mkdir()

    # Extract the sample study
    sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")
    with zipfile.ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=ext_workspace_path)

    # Generate a "config.yml" file for the app
    template_loader = jinja2.FileSystemLoader(searchpath=ASSETS_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("config.template.yml")

    config_path = tmp_path / "config.yml"
    launcher_name = "launcher_mock.bat" if RUN_ON_WINDOWS else "launcher_mock.sh"
    with open(config_path, "w") as fh:
        fh.write(
            template.render(
                db_url=db_url,
                default_workspace_path=str(default_workspace),
                ext_workspace_path=str(ext_workspace_path),
                matrix_dir=str(matrix_dir),
                archive_dir=str(archive_dir),
                tmp_dir=str(tmp_dir),
                launcher_mock=ASSETS_DIR / launcher_name,
            )
        )

    app, services = fastapi_app(config_path, RESOURCES_DIR, mount_front=False)
    yield app
    services.watcher.stop()


@pytest.fixture(name="client")
def client_fixture(app: FastAPI) -> TestClient:
    """Get the webservice client used for unit testing"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(name="admin_access_token")
def admin_access_token_fixture(client: TestClient) -> str:
    """Get the admin user access token used for authentication"""
    res = client.post(
        "/v1/login",
        json={"username": "admin", "password": "admin"},
    )
    res.raise_for_status()
    credentials = res.json()
    return t.cast(str, credentials["access_token"])


@pytest.fixture(name="user_access_token")
def user_access_token_fixture(
    client: TestClient,
    admin_access_token: str,
) -> str:
    """Get a classic user access token used for authentication"""
    res = client.post(
        "/v1/users",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={"name": "George", "password": "mypass"},
    )
    res.raise_for_status()
    res = client.post(
        "/v1/login",
        json={"username": "George", "password": "mypass"},
    )
    res.raise_for_status()
    credentials = res.json()
    return t.cast(str, credentials["access_token"])


@pytest.fixture(name="internal_study_id")
def internal_study_fixture(
    client: TestClient,
    user_access_token: str,
) -> str:
    """Get the ID of the internal study which is scanned by the watcher"""
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )
    res.raise_for_status()
    study_ids = t.cast(t.Iterable[str], res.json())
    return next(iter(study_ids))
