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
from typing import Iterable

import jinja2
import pytest
from _pytest.tmpdir import TempPathFactory
from fastapi import APIRouter, FastAPI
from sqlalchemy import create_engine
from starlette.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.logging.utils import LoggingMiddleware
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.core.utils.web import tags_metadata
from antarest.dbmodel import Base
from antarest.eventbus.web import ConnectionManager, connect_event_bus
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth, JwtSettings
from antarest.login.model import init_admin_user
from antarest.main import add_exception_handlers, register_all_routes
from antarest.service_creator import SESSION_ARGS, Services, create_services, store_services_on_app
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

    return db_path


@pytest.fixture(scope="session")
def app_with_routes(initial_db_file: Path, tmp_path_factory: TempPathFactory) -> tuple[FastAPI, ConnectionManager]:
    """
    Session-scoped fixture: creates the FastAPI app and registers all routes once.
    Services and DB are injected per-test via the `app` fixture below.

    Returns (application, ws_manager) so the per-test fixture can wire event buses.
    """
    from antarest import __version__
    from antarest.core.config import Config
    from antarest.core.logging.utils import configure_logger

    tmp_dir = tmp_path_factory.mktemp("session_app")
    config_path = tmp_dir / "config.yml"
    _render_config(config_path, f"sqlite:///{initial_db_file}", tmp_dir)
    config = Config.from_yaml_file(res=RESOURCES_DIR, file=config_path)
    configure_logger(config)

    application = FastAPI(
        title="AntaREST",
        version=__version__,
        docs_url=None,
        root_path=config.root_path,
        openapi_tags=tags_metadata,
        openapi_url=f"{config.api_prefix}/openapi.json",
    )

    api_root = APIRouter(prefix=config.api_prefix)
    ws_manager = register_all_routes(api_root, config)

    @AuthJWT.load_config  # type: ignore
    def get_jwt_config() -> JwtSettings:
        return JwtSettings(
            authjwt_secret_key=config.security.jwt_key,
            authjwt_token_location=("headers", "cookies"),
            authjwt_access_token_expires=Auth.ACCESS_TOKEN_DURATION,
            authjwt_refresh_token_expires=Auth.REFRESH_TOKEN_DURATION,
            authjwt_cookie_csrf_protect=False,
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    add_exception_handlers(application)

    # Add DB middleware to the stack (engine will be replaced per-test via DBSessionMiddleware(None, ...))
    placeholder_engine = create_engine(f"sqlite:///{initial_db_file}", connect_args={"check_same_thread": False})
    application.add_middleware(DBSessionMiddleware, custom_engine=placeholder_engine, session_args=SESSION_ARGS)
    DBSessionMiddleware(None, custom_engine=placeholder_engine, session_args=SESSION_ARGS)

    application.include_router(api_root)
    application.add_middleware(LoggingMiddleware)

    # Force Starlette to build and CACHE the middleware stack NOW.
    # In Starlette 0.24+, middleware_stack is lazily built on the first __call__.
    # build_middleware_stack() calls DBSessionMiddleware.__init__(placeholder_engine),
    # setting the global _Session. Caching it here ensures the stack is NOT rebuilt on
    # the first request, so per-test DBSessionMiddleware(None, per_test_engine) overrides
    # _Session correctly before any request arrives.
    application.middleware_stack = application.build_middleware_stack()

    return application, ws_manager


@pytest.fixture
def db_path(tmp_path: Path, initial_db_file: Path) -> Path:
    """
    We copy the base database file to the database file dedicated to each integration test.
    """
    db_path = tmp_path / "db.sqlite"
    shutil.copyfile(initial_db_file, db_path)
    return db_path


@pytest.fixture
def app_and_services(
    app_with_routes: tuple[FastAPI, ConnectionManager],
    tmp_path: Path,
    db_path: Path,
) -> Iterable[tuple[FastAPI, Services]]:
    application, ws_manager = app_with_routes
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

    from antarest.core.config import Config

    config = Config.from_yaml_file(res=RESOURCES_DIR, file=config_path)

    # Update the DB session global to point at the per-test DB engine
    per_test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    DBSessionMiddleware(None, custom_engine=per_test_engine, session_args=SESSION_ARGS)

    init_admin_user(engine=per_test_engine, session_args=SESSION_ARGS, admin_password=config.security.admin_pwd)
    services = create_services(config)

    # Wire event bus to the shared websocket manager
    connect_event_bus(services.event_bus, ws_manager)

    # Store services on the shared app so Depends() resolves them
    store_services_on_app(application, services, config)

    # Start the watcher so it scans the ext_workspace
    if services.watcher:
        services.watcher.start()

    def is_study_scanned():
        with db():
            studies = services.study.get_studies_information(
                StudyFilter(access_permissions=AccessPermissions.for_user(DEFAULT_ADMIN_USER))
            )
            return len(studies) == 1

    wait_for(is_study_scanned, timeout=10, sleep_time=0.01)

    yield application, services
    services.watcher.stop()


@pytest.fixture(name="app")
def app_fixture(app_and_services: tuple[FastAPI, Services]) -> FastAPI:
    return app_and_services[0]


@pytest.fixture
def services(app_and_services: tuple[FastAPI, Services]) -> Services:
    return app_and_services[1]


@pytest.fixture
def study_service(services: Services) -> StudyService:
    return services.study


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
