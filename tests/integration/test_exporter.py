from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.filesystem.factory import StudyFactory
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


def assert_url_content(request_handler: RequestHandler, url: str) -> bytes:
    app = create_server(request_handler)
    client = app.test_client()
    res = client.get(url)
    return res.data


def test_exporter_file(tmp_path: Path, sta_mini_zip_path: Path):

    path_studies = tmp_path / "studies"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    handler = RequestHandler(
        study_factory=StudyFactory(),
        exporter=Exporter(),
        path_studies=path_studies,
        path_resources=Mock(),
    )

    # data = assert_url_content(handler, url="/studies/STA-mini/export")
    # assert len(data) > 0

    # data = assert_url_content(handler, url="/studies/STA-mini/export?compact")
    data = handler.export_study("STA-mini", compact=True)
    assert len(data) > 0
