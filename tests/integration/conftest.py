import os
import shutil
from pathlib import Path
from zipfile import ZipFile

import jinja2
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from antarest import main
from antarest.main import fastapi_app
from tests.conftest import project_dir


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def app(tmp_path: str, sta_mini_zip_path: Path, project_path: Path):
    cur_dir: Path = Path(__file__).parent
    templateLoader = jinja2.FileSystemLoader(searchpath=cur_dir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "config.yml"
    template = templateEnv.get_template(TEMPLATE_FILE)

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
                launcher_mock=str(cur_dir / "launcher_mock.sh"),
            )
        )

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(project_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(
        db_url,
    )

    return fastapi_app(
        config_path, project_path / "resources", mount_front=False
    )
