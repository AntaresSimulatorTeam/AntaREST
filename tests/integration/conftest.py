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
import shutil
import time
import typing as t
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import jinja2
import pytest
from _pytest.tmpdir import TempPathFactory
from fastapi import FastAPI
from sqlalchemy import create_engine
from starlette.testclient import TestClient

from antarest.core.config import Config, ExternalAuthConfig, SecurityConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.dbmodel import Base
from antarest.login.model import init_admin_user
from antarest.main import _fastapi_app
from antarest.service_creator import SESSION_ARGS, Services, create_services, init_db_engine
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from tests.integration.assets import ASSETS_DIR

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")

RUN_ON_WINDOWS = os.name == "nt"


@dataclass
class ServicesSupplier:
    services: Services | None = None

    def get_services(self) -> Services:
        if self.services is None:
            raise ValueError("No services supplied")
        return self.services


@pytest.fixture(scope="session")
def services_supplier() -> ServicesSupplier:
    return ServicesSupplier()


@pytest.fixture(scope="session")
def global_config() -> Config:
    config = Config(
        security=SecurityConfig(
            disabled=False,
            jwt_key="super-secret",
            admin_pwd="admin",
            external_auth=ExternalAuthConfig(),
        )
    )
    return config


@pytest.fixture(scope="session")
def initial_db_file(tmp_path_factory: TempPathFactory) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"initial_db_file-{uuid.uuid4()}")
    db_path = tmp_dir / "db.sqlite"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

    return db_path


@pytest.fixture
def services(tmp_path: Path, initial_db_file: Path, services_supplier: ServicesSupplier) -> Iterable[Services]:
    # Currently, it is impossible to use a SQLite database in memory (with "sqlite:///:memory:")
    # because the database is created by the FastAPI application during each integration test,
    # which doesn't apply the migrations (migrations are done by Alembic).
    # An alternative is to use a SQLite database stored on disk, because migrations can be persisted.

    db_path = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_path}"

    shutil.copyfile(initial_db_file, db_path)

    # Prepare the directories used by the repos
    matrix_dir = tmp_path / "matrix_store"
    blob_dir = tmp_path / "blob_store"
    archive_dir = tmp_path / "archive_dir"
    tmp_dir = tmp_path / "tmp"
    default_workspace = tmp_path / "internal_workspace"
    ext_workspace_path = tmp_path / "ext_workspace"

    matrix_dir.mkdir()
    blob_dir.mkdir()
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
                blob_dir=str(blob_dir),
                archive_dir=str(archive_dir),
                tmp_dir=str(tmp_dir),
                launcher_mock=ASSETS_DIR / launcher_name,
            )
        )

    config = Config.from_yaml_file(res=RESOURCES_DIR, file=config_path)

    # database initialization
    engine = init_db_engine(config_path, config, False)
    init_db_singleton(custom_engine=engine, session_args=SESSION_ARGS)
    init_admin_user(engine=engine, session_args=SESSION_ARGS, admin_password=config.security.admin_pwd)

    # Services creation and starting
    services = create_services(config)
    services_supplier.services = services
    studies = []
    with db():
        while len(studies) != 1:
            studies = services.study.get_studies_information(
                StudyFilter(access_permissions=AccessPermissions.for_user(DEFAULT_ADMIN_USER))
            )
            time.sleep(0.01)
    yield services
    services.watcher.stop()
    services_supplier.services = None


@pytest.fixture(scope="session")
def app(services_supplier: ServicesSupplier, global_config: Config) -> FastAPI:
    return _fastapi_app(global_config, lambda: services_supplier.services, RESOURCES_DIR, mount_front=False)


@pytest.fixture
def study_service(services: Services) -> StudyService:
    return services.study


@pytest.fixture(name="client")
def client_fixture(app: FastAPI, services: Services) -> TestClient:
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
