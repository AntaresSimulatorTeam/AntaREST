from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.engine.url_engine import UrlNotMatchJsonDataError
from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
    RequestHandler,
)
from api_iso_antares.web.server import create_server


@pytest.mark.unit_test
def test_server() -> None:
    mock_handler = Mock()
    mock_handler.get.return_value = {}

    parameters = RequestHandlerParameters()

    app = create_server(mock_handler)
    client = app.test_client()
    client.get("/metadata/study1/settings/general/params")

    mock_handler.get.assert_called_once_with(
        "study1/settings/general/params", parameters
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_handler = Mock()
    mock_handler.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/metadata/study1/settings/general/params")
    assert result.status_code == 404

    result = client.get("/metadata/WRONG_STUDY")
    assert result.status_code == 404


@pytest.mark.unit_test
def test_server_with_parameters() -> None:

    mock_handler = Mock()
    mock_handler.get.return_value = {}

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/metadata/study1?depth=4")

    parameters = RequestHandlerParameters(depth=4)

    assert result.status_code == 200
    mock_handler.get.assert_called_once_with("study1", parameters)

    result = client.get("/metadata/study2?depth=WRONG_TYPE")

    excepted_parameters = RequestHandlerParameters()

    assert result.status_code == 200
    mock_handler.get.assert_called_with("study2", excepted_parameters)


@pytest.mark.unit_test
def test_matrix(tmp_path: str) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study1" / "matrix").write_text("toto")

    request_handler = RequestHandler(
        study_reader=Mock(), url_engine=Mock(), path_studies=Path(tmp_path)
    )
    app = create_server(request_handler)
    client = app.test_client()
    result_right = client.get("/data/study1/matrix")

    assert result_right.data == b"toto"

    result_wrong = client.get("/data/study1/WRONG_MATRIX")
    assert result_wrong.status_code == 404
