from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from storage_api.antares_io.exporter.export_file import Exporter
from storage_api.filesystem.factory import StudyFactory
from storage_api.web import RequestHandler
from storage_api.web.server import create_server


def assert_url_content(request_handler: RequestHandler, url: str) -> bytes:
    app = create_server(request_handler, res=Path())
    client = app.test_client()
    res = client.get(url)
    return res.data


def assert_data(data: bytes):
    assert len(data) > 0 and b"<!DOCTYPE HTML PUBLIC" not in data


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

    data = assert_url_content(handler, url="/studies/STA-mini/export")
    assert_data(data)

    data = assert_url_content(handler, url="/studies/STA-mini/export?compact")
    assert_data(data)


def test_exporter_file_no_output(tmp_path: Path, sta_mini_zip_path: Path):

    path_studies = tmp_path / "studies"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    handler = RequestHandler(
        study_factory=StudyFactory(),
        exporter=Exporter(),
        path_studies=path_studies,
        path_resources=Mock(),
    )

    data = assert_url_content(
        handler, url="/studies/STA-mini/export?no-output"
    )
    assert_data(data)

    data = assert_url_content(
        handler, url="/studies/STA-mini/export?compact&no-output"
    )
    assert_data(data)
