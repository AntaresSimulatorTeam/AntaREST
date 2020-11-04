from pathlib import Path
from typing import Callable
from unittest.mock import Mock
from http import HTTPStatus

import pytest

from api_iso_antares.engine.url_engine import UrlNotMatchJsonDataError
from api_iso_antares.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
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
def test_matrix(tmp_path: str, request_handler_builder: Callable) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study1" / "matrix").write_text("toto")

    request_handler = request_handler_builder(path_studies=tmp)

    app = create_server(request_handler)
    client = app.test_client()
    result_right = client.get("/file/study1/matrix")

    assert result_right.data == b"toto"

    result_wrong = client.get("/file/study1/WRONG_MATRIX")
    assert result_wrong.status_code == 404


@pytest.mark.unit_test
def test_create_study(
    tmp_path: str, request_handler_builder: Callable, project_path
) -> None:

    path_studies = Path(tmp_path)
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    study_parser = Mock()
    reader = Mock()
    reader.read.return_value = {"antares": {"caption": None}}
    study_parser.get_reader.return_value = reader

    request_handler = request_handler_builder(
        path_studies=path_studies,
        study_parser=study_parser,
        path_resources=project_path / "resources",
    )

    app = create_server(request_handler)
    client = app.test_client()

    result_wrong = client.post("/studies/study1")

    assert result_wrong.status_code == HTTPStatus.CONFLICT.value

    result_right = client.post("/studies/study2")

    assert result_right.status_code == HTTPStatus.CREATED.value
