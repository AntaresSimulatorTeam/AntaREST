import io
import json
import shutil
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Callable
from unittest.mock import Mock, call

import pytest
from flask import Flask
from markupsafe import Markup

from antarest import __version__
from antarest.common.config import Config
from antarest.login.model import User, Role
from antarest.storage.main import build_storage
from antarest.storage.web.exceptions import (
    IncorrectPathError,
    UrlNotMatchJsonDataError,
)
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)

ADMIN = User(id=0, name="admin", role=Role.ADMIN)


@pytest.mark.unit_test
def test_server() -> None:
    mock_service = Mock()
    mock_service.get.return_value = {}

    parameters = StorageServiceParameters(user=ADMIN)

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    client.get("/studies/study1/settings/general/params")

    mock_service.get.assert_called_once_with(
        "study1/settings/general/params", parameters
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_storage_service = Mock()
    mock_storage_service.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/studies/study1/settings/general/params")
    assert result.status_code == 404

    result = client.get("/studies/WRONG_STUDY")
    assert result.status_code == 404


@pytest.mark.unit_test
def test_server_with_parameters() -> None:

    mock_storage_service = Mock()
    mock_storage_service.get.return_value = {}

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/studies/study1?depth=4")

    parameters = StorageServiceParameters(depth=4, user=ADMIN)

    assert result.status_code == 200
    mock_storage_service.get.assert_called_once_with("study1", parameters)

    result = client.get("/studies/study2?depth=WRONG_TYPE")

    excepted_parameters = StorageServiceParameters(user=ADMIN)

    assert result.status_code == 200
    mock_storage_service.get.assert_called_with("study2", excepted_parameters)


@pytest.mark.unit_test
def test_matrix(tmp_path: str, storage_service_builder) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study1" / "matrix").write_text("toto")

    storage_service = Mock()
    storage_service.study_service.path_to_studies = tmp

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result_right = client.get("/file/study1/matrix")

    assert result_right.data == b"toto"

    result_wrong = client.get("/file/study1/WRONG_MATRIX")
    assert result_wrong.status_code == 404


@pytest.mark.unit_test
def test_create_study(
    tmp_path: str, storage_service_builder, project_path
) -> None:

    path_studies = Path(tmp_path)
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    storage_service = Mock()
    storage_service.create_study.return_value = "my-uuid"

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()

    result_right = client.post("/studies/study2")

    assert result_right.status_code == HTTPStatus.CREATED.value
    assert json.loads(result_right.data) == "/studies/my-uuid"
    storage_service.create_study.assert_called_once_with("study2")


@pytest.mark.unit_test
def test_import_study_zipped(
    tmp_path: Path, storage_service_builder, project_path
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

    mock_storage_service = Mock()
    mock_storage_service.import_study.return_value = study_name

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()

    result = client.post("/studies")

    assert result.status_code == HTTPStatus.BAD_REQUEST.value

    study_data = io.BytesIO(path_zip.read_bytes())
    result = client.post("/studies", data={"study": (study_data, "study.zip")})

    print(result.data)
    assert json.loads(result.data) == "/studies/" + study_name
    assert result.status_code == HTTPStatus.CREATED.value
    mock_storage_service.import_study.assert_called_once()


@pytest.mark.unit_test
def test_copy_study(tmp_path: Path, storage_service_builder) -> None:
    storage_service = Mock()
    storage_service.copy_study.return_value = "/studies/study-copied"

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()

    result = client.post("/studies/existing-study/copy?dest=study-copied")

    storage_service.copy_study.assert_called_with(
        src_uuid="existing-study", dest_study_name="study-copied"
    )
    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.unit_test
def test_list_studies(tmp_path: str, storage_service_builder) -> None:

    studies = {
        "study1": {"antares": {"caption": ""}},
        "study2": {"antares": {"caption": ""}},
    }

    storage_service = Mock()
    storage_service.get_studies_information.return_value = studies

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/studies")

    assert json.loads(result.data) == studies


@pytest.mark.unit_test
def test_server_health() -> None:
    app = Flask(__name__)
    build_storage(
        app,
        storage_service=Mock(),
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/health")
    assert result.data == b'{"status":"available"}\n'


@pytest.mark.unit_test
def test_export_files() -> None:

    mock_storage_service = Mock()
    mock_storage_service.export_study.return_value = BytesIO(b"Hello")

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/studies/name/export")

    assert result.data == b"Hello"
    mock_storage_service.export_study.assert_called_once_with(
        "name", False, True
    )


@pytest.mark.unit_test
def test_export_params() -> None:

    mock_storage_service = Mock()
    mock_storage_service.export_study.return_value = BytesIO(b"Hello")

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    result = client.get("/studies/name/export?compact")

    assert result.data == b"Hello"

    client.get("/studies/name/export?compact&no-output")
    client.get("/studies/name/export?compact=true&no-output=true")
    client.get("/studies/name/export?compact=false&no-output=false")
    client.get("/studies/name/export?no-output=false")
    mock_storage_service.export_study.assert_has_calls(
        [
            call(Markup("name"), True, True),
            call(Markup("name"), True, False),
            call(Markup("name"), True, False),
            call(Markup("name"), False, True),
            call(Markup("name"), False, True),
        ]
    )


@pytest.mark.unit_test
def test_delete_study() -> None:

    mock_storage_service = Mock()

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    client.delete("/studies/name")

    mock_storage_service.delete_study.assert_called_once_with("name")


@pytest.mark.unit_test
def test_import_matrix() -> None:
    mock_storage_service = Mock()

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    mock_storage_service.upload_matrix.assert_called_once_with(path, b"hello")
    assert result.status_code == HTTPStatus.NO_CONTENT.value


@pytest.mark.unit_test
def test_import_matrix_with_wrong_path() -> None:

    mock_storage_service = Mock()
    mock_storage_service.upload_matrix = Mock(
        side_effect=IncorrectPathError("")
    )

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    assert result.status_code == HTTPStatus.NOT_FOUND.value


@pytest.mark.unit_test
def test_edit_study() -> None:
    mock_storage_service = Mock()
    mock_storage_service.edit_study.return_value = {}

    data = json.dumps({"Hello": "World"})

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    client.post("/studies/my-uuid/url/to/change", data=data)

    mock_storage_service.edit_study.assert_called_once_with(
        "my-uuid/url/to/change", {"Hello": "World"}
    )


@pytest.mark.unit_test
def test_edit_study_fail() -> None:
    mock_storage_service = Mock()

    data = json.dumps({})

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=Config(
            {
                "_internal": {"resources_path": Path()},
                "security": {"disabled": True},
                "storage": {"studies": Path()},
            }
        ),
    )
    client = app.test_client()
    res = client.post("/studies/my-uuid/url/to/change", data=data)

    assert res.status_code == 400

    mock_storage_service.edit_study.assert_not_called()
