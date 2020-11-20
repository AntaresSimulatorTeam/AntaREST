from unittest.mock import Mock

from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


def assert_url_content(request_handler: RequestHandler, url: str) -> bytes:
    app = create_server(request_handler)
    client = app.test_client()
    res = client.get(url)
    return res.data


def test_exporter_file(project_path):
    studies = project_path / "examples/studies"

    handler = RequestHandler(
        study_parser=Mock(),
        url_engine=Mock(),
        exporter=Exporter(),
        path_studies=studies,
        path_resources=Mock(),
        jsm_validator=Mock(),
    )

    data = assert_url_content(handler, url="/exportation/sub-study")
    assert len(data) > 0

    data = assert_url_content(handler, url="/exportation/sub-study?compact")
    assert len(data) > 0
