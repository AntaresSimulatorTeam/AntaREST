from pathlib import Path
from zipfile import ZipFile

import pytest

from antarest.common.config import Config
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.web import RequestHandler


@pytest.fixture
def sta_mini_path(tmp_path: str) -> Path:
    return Path(tmp_path) / "studies" / "STA-mini"


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def request_handler(
    tmp_path: str, project_path: Path, sta_mini_zip_path: Path
) -> RequestHandler:

    path_studies = Path(tmp_path) / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    request_handler = RequestHandler(
        study_factory=StudyFactory(),
        exporter=Exporter(),
        config=Config(
            {
                "main": {"res": path_resources},
                "storage": {"studies": path_studies},
            }
        ),
    )

    return request_handler
