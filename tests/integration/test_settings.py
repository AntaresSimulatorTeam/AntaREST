import json
from pathlib import Path

import pytest
from unittest.mock import Mock

from api_iso_antares.antares_io.reader import IniReader, JsmReader
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


@pytest.mark.integration_test
def test_request(tmp_path: str) -> None:

    project_dir: Path = Path(__file__).resolve().parents[2]

    path_to_schema = (
        project_dir / "examples/jsonschemas/sub-study/jsonschema.json"
    )
    jsm = JsmReader.read(path_to_schema)

    jsm_validator = JsmValidator(jsm=jsm)

    readers = {"default": IniReader()}
    writers = {"default": Mock()}
    study_reader = FileSystemEngine(jsm=jsm, readers=readers, writers=writers)

    studies_path = project_dir / "examples/studies"
    request_handler = RequestHandler(
        study_parser=study_reader,
        url_engine=UrlEngine(jsm={}),
        exporter=Mock(),
        path_studies=studies_path,
        path_resources=project_dir / "resources",
        jsm_validator=jsm_validator,
    )

    app = create_server(request_handler)
    client = app.test_client()
    res = client.get(
        "/studies/sub-study/settings/generaldata.ini/general/nbyears"
    )

    assert json.loads(res.data) == 2
