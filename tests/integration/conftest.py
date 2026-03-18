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
import shutil
import sys
import typing as t
import uuid
import zipfile
from pathlib import Path
from typing import Generator

import jinja2
import pytest
from _pytest.tmpdir import TempPathFactory
from fastapi import FastAPI
from sqlalchemy import create_engine
from starlette.testclient import TestClient

from antarest.core.config import Config
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.login.model import init_admin_user
from antarest.main import (
    base_fastapi_app,
    init_db,
    inject_services,
)
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_for

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")

RUN_ON_WINDOWS = sys.platform == "win32"


def _render_config(config_path: Path, db_url: str, tmp_path: Path) -> None:
    matrix_dir = tmp_path / "matrix_store"
    blob_dir = tmp_path / "blob_store"
    archive_dir = tmp_path / "archive_dir"
    tmp_dir = tmp_path / "tmp"
    default_workspace = tmp_path / "internal_workspace"
    ext_workspace_path = tmp_path / "ext_workspace"
    output_archive_dir = tmp_path / "output_archives"

    for d in (matrix_dir, blob_dir, archive_dir, tmp_dir, default_workspace, ext_workspace_path):
        d.mkdir(exist_ok=True)

    template_loader = jinja2.FileSystemLoader(searchpath=ASSETS_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("config.template.yml")

    launcher_name = "launcher_mock.bat" if RUN_ON_WINDOWS else "launcher_mock.sh"
    with open(config_path, "w") as fh:
        fh.write(
            template.render(
                db_url=db_url,
                default_workspace_path=str(default_workspace),
                ext_workspace_path=str(ext_workspace_path),
                matrix_dir=str(matrix_dir),
                blob_dir=str(blob_dir),
                archive_dir=str(archive_dir),
                tmp_dir=str(tmp_dir),
                launcher_mock=ASSETS_DIR / launcher_name,
                output_archive_dir=str(output_archive_dir),
            )
        )


@pytest.fixture(scope="session")
def initial_db_file(tmp_path_factory: TempPathFactory) -> Path:
    """
    Initializing the database schema is a costly operation: we perform it only once
    here for the test session, and then copy the database file to each integration test.
    """
    tmp_dir = tmp_path_factory.mktemp(basename=f"initial_db_file-{uuid.uuid4()}")
    db_path = tmp_dir / "db.sqlite"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

    init_admin_user(engine, {}, "admin")

    return db_path


@pytest.fixture(scope="session")
def base_app(tmp_path_factory: TempPathFactory) -> FastAPI:
    return base_fastapi_app("", "")


@pytest.fixture
def db_path(tmp_path: Path, initial_db_file: Path) -> Path:
    """
    We copy the base database file to the database file dedicated to each integration test.
    """
    db_path = tmp_path / "db.sqlite"
    shutil.copyfile(initial_db_file, db_path)
    return db_path


def _get_from_container(app: FastAPI, service_type: type):
    """Synchronously retrieve a service from the dishka container attached to the app."""
    import asyncio

    container = app.state.dishka_container

    async def _get():
        return await container.get(service_type)

    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(_get())
    except RuntimeError:
        return asyncio.run(_get())


@pytest.fixture
def app_fixture_inner(base_app: FastAPI, tmp_path: Path, db_path: Path) -> Generator[FastAPI, None, None]:
    app = base_app

    db_url = f"sqlite:///{db_path}"

    # Extract the sample study into the per-test ext_workspace
    ext_workspace_path = tmp_path / "ext_workspace"
    ext_workspace_path.mkdir(exist_ok=True)
    sta_mini_zip_path = ASSETS_DIR.joinpath("STA-mini.zip")
    with zipfile.ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=ext_workspace_path)

    # Generate a per-test config with proper workspace paths
    config_path = tmp_path / "config.yml"
    _render_config(config_path, db_url, tmp_path)
    config = Config.from_yaml_file(res=RESOURCES_DIR, file=config_path)
    init_db(config, config_path, auto_upgrade=False, init_admin=False)
    inject_services(app, config)

    from antarest.study.storage.rawstudy.watcher import Watcher

    watcher = _get_from_container(app, Watcher)
    study_service = _get_from_container(app, StudyService)

    # Start the watcher so it scans the ext_workspace
    watcher.start()

    def is_study_scanned():
        with db():
            studies = study_service.get_studies_information(
                StudyFilter(access_permissions=AccessPermissions.for_user(DEFAULT_ADMIN_USER))
            )
            return len(studies) == 1

    wait_for(is_study_scanned, timeout=10, sleep_time=0.01)

    yield app
    watcher.stop()


@pytest.fixture(name="app")
def app_fixture(app_fixture_inner: FastAPI) -> FastAPI:
    return app_fixture_inner


@pytest.fixture
def study_service(app: FastAPI) -> StudyService:
    return _get_from_container(app, StudyService)


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


@pytest.fixture
def admin_client(client: TestClient, admin_access_token: str) -> TestClient:
    headers = {"Authorization": f"Bearer {admin_access_token}"}
    client.headers.update(headers)
    return client


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
