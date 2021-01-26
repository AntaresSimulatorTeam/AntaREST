import io
import json
import shutil
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from storage_api import __version__
from storage_api.web.html_exception import (
    IncorrectPathError,
    UrlNotMatchJsonDataError,
)
from storage_api.web.request_handler import (
    RequestHandlerParameters,
)
from storage_api.web.server import (
    create_server,
)


@pytest.mark.unit_test
def test_server() -> None:
    mock_handler = Mock()
    mock_handler.get.return_value = {}

    parameters = RequestHandlerParameters()

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    client.get("/studies/study1/settings/general/params")

    mock_handler.get.assert_called_once_with(
        "study1/settings/general/params", parameters
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_handler = Mock()
    mock_handler.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    result = client.get("/studies/study1/settings/general/params")
    assert result.status_code == 404

    result = client.get("/studies/WRONG_STUDY")
    assert result.status_code == 404


@pytest.mark.unit_test
def test_server_with_parameters() -> None:

    mock_handler = Mock()
    mock_handler.get.return_value = {}

    app = create_server(mock_handler, res=Path())
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

    app = create_server(request_handler, res=Path())
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

    request_handler = Mock()
    request_handler.create_study.return_value = "my-uuid"

    app = create_server(request_handler, res=Path())
    client = app.test_client()

    result_right = client.post("/studies/study2")

    assert result_right.status_code == HTTPStatus.CREATED.value
    assert json.loads(result_right.data) == "/studies/my-uuid"
    request_handler.create_study.assert_called_once_with("study2")


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
    app = create_server(mock_request_handler, res=Path())
    client = app.test_client()

    result = client.post("/studies")

    assert result.status_code == HTTPStatus.BAD_REQUEST.value

    study_data = io.BytesIO(path_zip.read_bytes())
    result = client.post("/studies", data={"study": (study_data, "study.zip")})

    print(result.data)
    assert json.loads(result.data) == "/studies/" + study_name
    assert result.status_code == HTTPStatus.CREATED.value
    mock_request_handler.import_study.assert_called_once()


@pytest.mark.unit_test
def test_copy_study(tmp_path: Path, request_handler_builder: Callable) -> None:
    request_handler = Mock()
    request_handler.copy_study.return_value = "/studies/study-copied"

    app = create_server(request_handler, res=Path())
    client = app.test_client()

    result = client.post("/studies/existing-study/copy?dest=study-copied")

    request_handler.copy_study.assert_called_with(
        src_uuid="existing-study", dest_study_name="study-copied"
    )
    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.unit_test
def test_list_studies(
    tmp_path: str, request_handler_builder: Callable
) -> None:

    studies = {
        "study1": {"antares": {"caption": ""}},
        "study2": {"antares": {"caption": ""}},
    }

    request_handler = Mock()
    request_handler.get_studies_informations.return_value = studies

    app = create_server(request_handler, res=Path())
    client = app.test_client()
    result = client.get("/studies")

    assert json.loads(result.data) == studies


@pytest.mark.unit_test
def test_server_health() -> None:
    app = create_server(Mock(), res=Path())
    client = app.test_client()
    result = client.get("/health")
    assert result.data == b'{"status":"available"}\n'


@pytest.mark.unit_test
def test_export_files() -> None:

    mock_handler = Mock()
    mock_handler.export_study.return_value = BytesIO(b"Hello")

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    result = client.get("/studies/name/export")

    assert result.data == b"Hello"
    mock_handler.export_study.assert_called_once_with("name", False, True)


@pytest.mark.unit_test
def test_export_compact() -> None:

    mock_handler = Mock()
    mock_handler.export_study.return_value = BytesIO(b"Hello")

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    result = client.get("/studies/name/export?compact")

    assert result.data == b"Hello"
    mock_handler.export_study.assert_called_once_with("name", True, True)


@pytest.mark.unit_test
def test_delete_study() -> None:

    mock_handler = Mock()

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    client.delete("/studies/name")

    mock_handler.delete_study.assert_called_once_with("name")


@pytest.mark.unit_test
def test_import_matrix() -> None:
    mock_handler = Mock()

    app = create_server(mock_handler, res=Path())
    client = app.test_client()

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    mock_handler.upload_matrix.assert_called_once_with(path, b"hello")
    assert result.status_code == HTTPStatus.NO_CONTENT.value


@pytest.mark.unit_test
def test_import_matrix_with_wrong_path() -> None:

    mock_handler = Mock()
    mock_handler.upload_matrix = Mock(side_effect=IncorrectPathError(""))

    app = create_server(mock_handler, res=Path())
    client = app.test_client()

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    assert result.status_code == HTTPStatus.NOT_FOUND.value


@pytest.mark.unit_test
def test_edit_study() -> None:
    mock_handler = Mock()
    mock_handler.edit_study.return_value = {}

    data = json.dumps({"Hello": "World"})

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    client.post("/studies/my-uuid/url/to/change", data=data)

    mock_handler.edit_study.assert_called_once_with(
        "my-uuid/url/to/change", {"Hello": "World"}
    )


@pytest.mark.unit_test
def test_edit_study_fail() -> None:
    mock_handler = Mock()

    data = json.dumps({})

    app = create_server(mock_handler, res=Path())
    client = app.test_client()
    res = client.post("/studies/my-uuid/url/to/change", data=data)

    assert res.status_code == 400

    mock_handler.edit_study.assert_not_called()
