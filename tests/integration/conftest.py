import os
import time
from multiprocessing import Process
from pathlib import Path
from zipfile import ZipFile

import jinja2
import pytest
import requests
import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from antarest.main import fastapi_app
from tests.conftest import project_dir


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


def app_builder(
    tmp_path: str,
    sta_mini_zip_path: Path,
    project_path: Path,
    mount_front: bool,
):
    cur_dir: Path = Path(__file__).parent
    templateLoader = jinja2.FileSystemLoader(searchpath=cur_dir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "config.yml"
    template = templateEnv.get_template(TEMPLATE_FILE)

    matrix_dir = Path(tmp_path) / "matrixstore"
    os.mkdir(matrix_dir)
    archive_dir = Path(tmp_path) / "archive_dir"
    os.mkdir(archive_dir)
    tmp_dir = Path(tmp_path) / "tmp"
    os.mkdir(tmp_dir)
    default_workspace = Path(tmp_path) / "internal_workspace"
    os.mkdir(default_workspace)
    ext_workspace_path = Path(tmp_path) / "ext_workspace"
    os.mkdir(ext_workspace_path)
    config_path = Path(tmp_path) / "config.yml"
    db_path = Path(tmp_path) / "db.sqlite"
    db_path.touch()
    db_url = "sqlite:///" + str(db_path)

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=ext_workspace_path)

    with open(config_path, "w") as fh:
        fh.write(
            template.render(
                dburl=db_url,
                default_workspace_path=str(default_workspace),
                ext_workspace_path=str(ext_workspace_path),
                matrix_dir=str(matrix_dir),
                archive_dir=str(archive_dir),
                tmp_dir=str(tmp_dir),
                launcher_mock=str(cur_dir / "launcher_mock.sh"),
            )
        )

    alembic_cfg = Config()
    alembic_cfg.set_main_option(
        "script_location", str(project_dir / "alembic")
    )
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    app, _ = fastapi_app(
        config_path, project_path / "resources", mount_front=mount_front
    )
    return app


@pytest.fixture
def app(tmp_path: str, sta_mini_zip_path: Path, project_path: Path):
    return app_builder(tmp_path, sta_mini_zip_path, project_path, False)


@pytest.fixture
def app_with_front(tmp_path: str, sta_mini_zip_path: Path, project_path: Path):
    return app_builder(tmp_path, sta_mini_zip_path, project_path, True)


def run_server(app_with_front: FastAPI):
    uvicorn.run(app_with_front, host="0.0.0.0", port=8080)


@pytest.fixture
def running_app_with_ui(app_with_front: FastAPI):
    server = Process(
        target=run_server,
        args=(app_with_front,),
    )
    server.start()
    countdown = 10
    while countdown > 0:
        try:
            res = requests.get("http://localhost:8080")
            if res.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
        countdown -= 1

    yield server
    server.kill()
