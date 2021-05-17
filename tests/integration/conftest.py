import os
import shutil
from pathlib import Path

import jinja2
import pytest

from antarest.main import flask_app


@pytest.fixture
def app(tmp_path: str):
    cur_dir: Path = Path(__file__).parent
    templateLoader = jinja2.FileSystemLoader(searchpath=cur_dir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "config.yml"
    template = templateEnv.get_template(TEMPLATE_FILE)

    default_workspace = Path(tmp_path) / "internal_workspace"
    ext_workspace_path = Path(tmp_path) / "ext_workspace"
    config_path = Path(tmp_path) / "config.yml"
    db_path = Path(tmp_path) / "db.sqlite"
    db_path.touch()
    db_url = "sqlite:///" + str(db_path)

    with open(config_path, "w") as fh:
        fh.write(
            template.render(
                dburl=db_url,
                default_workspace_path=str(default_workspace),
                ext_workspace_path=str(ext_workspace_path),
                launcher_mock=str(cur_dir / "launcher_mock.py")
            )
        )

    return flask_app(config_path)