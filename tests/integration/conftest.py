from pathlib import Path
from typing import cast
from zipfile import ZipFile

import jinja2
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from starlette.testclient import TestClient

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.main import fastapi_app
from antarest.study.storage.rawstudy.watcher import Watcher
from tests.integration.assets import ASSETS_DIR

# fmt: off
HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")
# fmt: on


@pytest.fixture(name="app")
def app_fixture(tmp_path: Path):
    # First, create a database and apply migrations
    db_path = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

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
    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=ext_workspace_path)

    # Generate a "config.yml" file for the app
    template_loader = jinja2.FileSystemLoader(searchpath=ASSETS_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("config.template.yml")

    config_path = tmp_path / "config.yml"
    with open(config_path, "w") as fh:
        fh.write(
            template.render(
                db_url=db_url,
                default_workspace_path=str(default_workspace),
                ext_workspace_path=str(ext_workspace_path),
                matrix_dir=str(matrix_dir),
                archive_dir=str(archive_dir),
                tmp_dir=str(tmp_dir),
                launcher_mock=ASSETS_DIR / "launcher_mock.sh",
            )
        )

    app, services = fastapi_app(config_path, RESOURCES_DIR, mount_front=False)
    yield app
    cast(Watcher, services["watcher"]).stop()


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
    return credentials["access_token"]


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
    return credentials["access_token"]


@pytest.fixture(name="study_id")
def study_id_fixture(
    client: TestClient,
    user_access_token: str,
) -> str:
    """Get the ID of the study stored in database"""
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )
    res.raise_for_status()
    study_ids = res.json()
    return next(iter(study_ids))
