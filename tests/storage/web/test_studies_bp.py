import io
import json
import shutil
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from flask import Flask
from markupsafe import Markup

from antarest.common.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.main import build_storage
from antarest.storage.model import DEFAULT_WORKSPACE_NAME, PublicMode
from antarest.storage.web.exceptions import (
    IncorrectPathError,
    UrlNotMatchJsonDataError,
)
from antarest.common.requests import (
    RequestParameters,
)

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)
PARAMS = RequestParameters(user=ADMIN)


CONFIG = Config(
    resources_path=Path(),
    security=SecurityConfig(disabled=True),
    storage=StorageConfig(
        workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=Path())}
    ),
)


@pytest.mark.unit_test
def test_server() -> None:
    mock_service = Mock()
    mock_service.get.return_value = {}

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_service,
        session=Mock(),
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    client.get("/studies/study1/settings/general/params")

    mock_service.get.assert_called_once_with(
        "study1/settings/general/params", 3, PARAMS
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
        config=CONFIG,
        user_service=Mock(),
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    result = client.get("/studies/study1?depth=4")

    parameters = RequestParameters(user=ADMIN)

    assert result.status_code == 200
    mock_storage_service.get.assert_called_once_with("study1", 4, parameters)

    result = client.get("/studies/study2?depth=WRONG_TYPE")

    excepted_parameters = RequestParameters(user=ADMIN)

    assert result.status_code == 200
    mock_storage_service.get.assert_called_with(
        "study2", 3, excepted_parameters
    )


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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()

    result_right = client.post("/studies/study2")

    assert result_right.status_code == HTTPStatus.CREATED.value
    assert json.loads(result_right.data) == "/studies/my-uuid"
    storage_service.create_study.assert_called_once_with("study2", PARAMS)


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
        config=CONFIG,
        user_service=Mock(),
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()

    result = client.post("/studies/existing-study/copy?dest=study-copied")

    storage_service.copy_study.assert_called_with(
        src_uuid="existing-study",
        dest_study_name="study-copied",
        params=PARAMS,
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
        config=CONFIG,
        user_service=Mock(),
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
        config=CONFIG,
        user_service=Mock(),
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    result = client.get("/studies/name/export")

    assert result.data == b"Hello"
    mock_storage_service.export_study.assert_called_once_with(
        "name", PARAMS, False, True
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
        config=CONFIG,
        user_service=Mock(),
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
            call(Markup("name"), PARAMS, True, True),
            call(Markup("name"), PARAMS, True, False),
            call(Markup("name"), PARAMS, True, False),
            call(Markup("name"), PARAMS, False, True),
            call(Markup("name"), PARAMS, False, True),
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    client.delete("/studies/name")

    mock_storage_service.delete_study.assert_called_once_with("name", PARAMS)


@pytest.mark.unit_test
def test_import_matrix() -> None:
    mock_storage_service = Mock()

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        session=Mock(),
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    mock_storage_service.upload_matrix.assert_called_once_with(
        path, b"hello", PARAMS
    )
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
        config=CONFIG,
        user_service=Mock(),
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    client.post("/studies/my-uuid/url/to/change", data=data)

    mock_storage_service.edit_study.assert_called_once_with(
        "my-uuid/url/to/change", {"Hello": "World"}, PARAMS
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
        config=CONFIG,
        user_service=Mock(),
    )
    client = app.test_client()
    res = client.post("/studies/my-uuid/url/to/change", data=data)

    assert res.status_code == 400

    mock_storage_service.edit_study.assert_not_called()


@pytest.mark.unit_test
def test_study_permission_management(
    tmp_path: Path, storage_service_builder
) -> None:
    storage_service = Mock()

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        user_service=Mock(),
        config=CONFIG,
    )
    client = app.test_client()

    result = client.put("/studies/existing-study/owner/2")
    storage_service.change_owner.assert_called_with(
        "existing-study",
        2,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/studies/existing-study/groups/group-a")
    storage_service.add_group.assert_called_with(
        "existing-study",
        "group-a",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.delete("/studies/existing-study/groups/group-b")
    storage_service.remove_group.assert_called_with(
        "existing-study",
        "group-b",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/studies/existing-study/public_mode/FULL")
    storage_service.set_public_mode.assert_called_with(
        "existing-study",
        PublicMode.FULL,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/studies/existing-study/public_mode/UNKNOWN")
    assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value
