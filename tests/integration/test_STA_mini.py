import json
import os
from pathlib import Path
from zipfile import ZipFile

import pytest
from flask.testing import FlaskClient

from api_iso_antares.antares_io.reader import (
    FolderReaderEngine,
    IniReader,
    JsmReader,
)
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


def assert_url_content(
    client: FlaskClient, url: str, expected_output: str
) -> None:
    res = client.get(url)
    assert json.loads(res.data) == expected_output


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url,expected_output",
    [
        (
            "/metadata/STA-mini/Desktop.ini/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/metadata/STA-mini/settings/generaldata.ini/general/horizon", 2030),
        (
            "/metadata/STA-mini/settings/comments.txt",
            f"file{os.sep}STA-mini{os.sep}settings{os.sep}comments.txt",
        ),
    ],
)
def test_sta_mini(
    tmp_path: str, project_path: Path, url: str, expected_output: str
) -> None:

    path_zip_STA = project_path / "examples/studies/STA-mini.zip"

    path_studies = Path(tmp_path) / "studies"

    with ZipFile(path_zip_STA) as zip_output:
        zip_output.extractall(path=path_studies)

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

    # url = url[10:]
    # print(url)
    # assert (
    #     request_handler.get(route=url, parameters=RequestHandlerParameters())
    #     == expected_output
    # )

    app = create_server(request_handler)
    client = app.test_client()
    assert_url_content(client=client, url=url, expected_output=expected_output)
