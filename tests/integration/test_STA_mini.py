import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.antares_io.reader import (
    FolderReaderEngine,
    IniReader,
    JsmReader,
)
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


@pytest.mark.integration_test
def test_sta_mini(tmp_path: str, project_path: Path) -> None:

    path_zip_STA = project_path / "examples/studies/STA-mini.zip"

    path_studies = Path(tmp_path) / "studies"

    with ZipFile(path_zip_STA) as zip_output:
        zip_output.extractall(path=path_studies)

    path_STA = path_studies / "STA-mini"
    path_jsm = project_path / "examples/jsonschemas/STA-mini/jsonschema.json"

    jsm = JsmReader.read(path_jsm)
    jsm_validator = JsmValidator(jsm=jsm)

    request_handler = RequestHandler(
        study_reader=FolderReaderEngine(
            ini_reader=IniReader(),
            jsm=jsm,
            root=path_studies,
            jsm_validator=jsm_validator,
        ),
        url_engine=UrlEngine(jsm=jsm),
        path_studies=path_studies,
    )

    app = create_server(request_handler)
    client = app.test_client()
    res = client.get("/metadata/STA-mini/Desktop.ini/.shellclassinfo/infotip")

    assert json.loads(res.data) == "Antares Study7.0: STA-mini"
