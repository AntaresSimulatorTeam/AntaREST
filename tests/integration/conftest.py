from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.antares_io.reader import IniReader, JsmReader
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.antares_io.writer.ini_writer import IniWriter
from api_iso_antares.antares_io.writer.matrix_writer import MatrixWriter
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.filesystem.factory import StudyFactory
from api_iso_antares.web import RequestHandler


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
        path_studies=path_studies,
        path_resources=path_resources,
    )

    return request_handler
