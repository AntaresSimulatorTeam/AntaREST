from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from flask import Flask

from antarest.common.config import Config
from antarest.storage_api.antares_io.exporter.export_file import Exporter
from antarest.storage_api.filesystem.factory import StudyFactory
from antarest.storage_api.main import build_storage
from antarest.storage_api.web import RequestHandler


def assert_url_content(request_handler: RequestHandler, url: str) -> bytes:
    app = Flask(__name__)
    build_storage(
        app,
        req=request_handler,
        config=Config({"main": {"res": request_handler.path_resources}}),
    )
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
        config=Config(
            {"main": {"res": Path()}, "storage": {"studies": path_studies}}
        ),
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
        config=Config(
            {"main": {"res": Path()}, "storage": {"studies": path_studies}}
        ),
    )

    data = assert_url_content(
        handler, url="/studies/STA-mini/export?no-output"
    )
    assert_data(data)

    data = assert_url_content(
        handler, url="/studies/STA-mini/export?compact&no-output"
    )
    assert_data(data)
