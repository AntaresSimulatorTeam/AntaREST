from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.antares_io.reader import IniReader, JsmReader
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.web import RequestHandler


@pytest.fixture
def path_jsm(project_path: Path) -> Path:
    return project_path / "examples/jsonschemas/STA-mini/jsonschema.json"


@pytest.fixture
def request_handler(
    tmp_path: str, project_path: Path, path_jsm: Path
) -> RequestHandler:

    path_zip_STA = project_path / "examples/studies/STA-mini.zip"

    path_studies = Path(tmp_path) / "studies"

    path_resources = project_path / "resources"

    with ZipFile(path_zip_STA) as zip_output:
        zip_output.extractall(path=path_studies)

    jsm = JsmReader.read(path_jsm)
    jsm_validator = JsmValidator(jsm=jsm)

    readers = {"default": IniReader()}
    study_reader = FileSystemEngine(jsm=jsm, readers=readers)

    request_handler = RequestHandler(
        study_parser=study_reader,
        url_engine=UrlEngine(jsm=jsm),
        path_studies=path_studies,
        path_resources=path_resources,
        jsm_validator=jsm_validator,
    )

    return request_handler
