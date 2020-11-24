import io
import json
import shutil
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
)
from api_iso_antares.web.html_exception import (
    IncorrectPathError,
    UrlNotMatchJsonDataError,
)
from api_iso_antares.web.server import (
    _assert_uuid,
    BadUUIDError,
    create_server,
)


@pytest.mark.unit_test
def test_server() -> None:
    mock_handler = Mock()
    mock_handler.get.return_value = {}

    parameters = RequestHandlerParameters()

    app = create_server(mock_handler)
    client = app.test_client()
    client.get("/studies/study1/settings/general/params")

    mock_handler.get.assert_called_once_with(
        "study1/settings/general/params", parameters
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_handler = Mock()
    mock_handler.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/studies/study1/settings/general/params")
    assert result.status_code == 404

    result = client.get("/studies/WRONG_STUDY")
    assert result.status_code == 404


@pytest.mark.unit_test
def test_server_with_parameters() -> None:

    mock_handler = Mock()
    mock_handler.get.return_value = {}

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/studies/study1?depth=4")

    parameters = RequestHandlerParameters(depth=4)

    assert result.status_code == 200
    mock_handler.get.assert_called_once_with("study1", parameters)

    result = client.get("/studies/study2?depth=WRONG_TYPE")

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
def test_post_study(
    tmp_path: str, request_handler_builder: Callable, project_path
) -> None:

    path_studies = Path(tmp_path)
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    study_parser = Mock()
    study_parser.parse.return_value = {"study": {"antares": {"caption": None}}}

    request_handler = request_handler_builder(
        path_studies=path_studies,
        study_parser=study_parser,
        path_resources=project_path / "resources",
    )

    app = create_server(request_handler)
    client = app.test_client()

    result_right = client.post("/studies/study2")

    assert result_right.status_code == HTTPStatus.CREATED.value

    result_wrong = client.post("/studies/%BAD_STUDY_NAME%")

    assert result_wrong.status_code == HTTPStatus.BAD_REQUEST.value


@pytest.mark.unit_test
def test_import_study_zipped(
    tmp_path: Path, request_handler_builder: Callable, project_path
) -> None:

    tmp_path /= "tmp"
    tmp_path.mkdir()
    study_name = "study1"
    path_study = tmp_path / study_name
    path_study.mkdir()
    path_file = path_study / "study.antares"
    path_file.write_text("[antares]")

    shutil.make_archive(path_study, "zip", path_study)
    path_zip = tmp_path / "study1.zip"

    mock_request_handler = Mock()
    mock_request_handler.import_study.return_value = study_name
    app = create_server(mock_request_handler)
    client = app.test_client()

    result = client.post("/studies")

    assert result.status_code == HTTPStatus.BAD_REQUEST.value

    study_data = io.BytesIO(path_zip.read_bytes())
    result = client.post("/studies", data=study_data)

    assert json.loads(result.data) == "/studies/" + study_name
    assert result.status_code == HTTPStatus.CREATED.value
    mock_request_handler.import_study.assert_called_once()


@pytest.mark.unit_test
def test_copy_study(tmp_path: Path, request_handler_builder: Callable) -> None:

    path_studies = tmp_path
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()
    path_study = path_studies / "study2"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    study_parser = Mock()
    study_parser.parse.return_value = {"study": {"antares": {"caption": None}}}

    request_handler = request_handler_builder(
        path_studies=path_studies, study_parser=study_parser
    )

    app = create_server(request_handler)
    client = app.test_client()

    result = client.post("/studies/%%%%/copy?dest=study")

    assert result.status_code == HTTPStatus.BAD_REQUEST.value

    result = client.post("/studies/study1/copy")

    assert result.status_code == HTTPStatus.BAD_REQUEST.value

    result = client.post("/studies/study3/copy?dest=study4")

    assert result.status_code == HTTPStatus.NOT_FOUND.value

    result = client.post("/studies/study1/copy?dest=study3")

    request_handler.copy_study("study1", "study3")
    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.unit_test
def test_list_studies(
    tmp_path: str, request_handler_builder: Callable
) -> None:

    path_studies = Path(tmp_path)
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()
    path_study = path_studies / "study2"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    url_engine = Mock()
    url_engine.apply.return_value = {"antares": {"caption": ""}}

    request_handler = request_handler_builder(
        path_studies=path_studies,
        url_engine=url_engine,
    )

    app = create_server(request_handler)
    client = app.test_client()
    result = client.get("/studies")
    studies = json.loads(result.data)

    expected_studies = {
        "study1": {"antares": {"caption": ""}},
        "study2": {"antares": {"caption": ""}},
    }

    assert studies == expected_studies


@pytest.mark.unit_test
def test_server_health() -> None:
    app = create_server(Mock())
    client = app.test_client()
    result = client.get("/health")
    assert result.data == b'{"status":"available"}\n'


@pytest.mark.unit_test
def test_export_files() -> None:

    mock_handler = Mock()
    mock_handler.export_study.return_value = BytesIO(b"Hello")

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/studies/name/export")

    assert result.data == b"Hello"
    mock_handler.export_study.assert_called_once_with("name", False)

    result_wrong = client.get("/studies/%BAD_STUDY_NAME%/export")
    assert result_wrong.status_code == HTTPStatus.BAD_REQUEST.value


@pytest.mark.unit_test
def test_export_compact() -> None:

    mock_handler = Mock()
    mock_handler.export_study.return_value = BytesIO(b"Hello")

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/studies/name/export?compact")

    assert result.data == b"Hello"
    mock_handler.export_study.assert_called_once_with("name", True)


@pytest.mark.unit_test
def test_bad_uuid() -> None:
    with pytest.raises(BadUUIDError):
        _assert_uuid("<toto")


@pytest.mark.unit_test
def test_delete_study() -> None:

    mock_handler = Mock()

    app = create_server(mock_handler)
    client = app.test_client()
    client.delete("/studies/name")

    mock_handler.delete_study.assert_called_once_with("name")
