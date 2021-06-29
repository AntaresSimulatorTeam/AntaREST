import io
import json
import shutil
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from fastapi import FastAPI
from markupsafe import Markup
from starlette.testclient import TestClient

from antarest.common.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.main import build_storage
from antarest.storage.model import (
    DEFAULT_WORKSPACE_NAME,
    PublicMode,
    StudyDownloadDTO,
    MatrixAggregationResult,
    MatrixIndex,
    StudySimResultDTO,
    StudySimSettingsDTO,
)
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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    client.get("/v1/studies/study1/raw?path=settings/general/params")

    mock_service.get.assert_called_once_with(
        "study1", "settings/general/params", 3, PARAMS
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_storage_service = Mock()
    mock_storage_service.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    result = client.get("/v1/studies/study1/raw?path=settings/general/params")
    assert result.status_code == 404

    result = client.get("/v1/studies/WRONG_STUDY/raw")
    assert result.status_code == 404


@pytest.mark.unit_test
def test_server_with_parameters() -> None:
    mock_storage_service = Mock()
    mock_storage_service.get.return_value = {}

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/study1/raw?depth=4")

    parameters = RequestParameters(user=ADMIN)

    assert result.status_code == 200
    mock_storage_service.get.assert_called_once_with(
        "study1", "/", 4, parameters
    )

    result = client.get("/v1/studies/study2/raw?depth=WRONG_TYPE")

    assert result.status_code == 422

    result = client.get("/v1/studies/study2/raw")

    excepted_parameters = RequestParameters(user=ADMIN)
    mock_storage_service.get.assert_called_with(
        "study2", "/", 3, excepted_parameters
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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)

    result_right = client.post("/v1/studies?name=study2")

    assert result_right.status_code == HTTPStatus.CREATED.value
    assert result_right.json() == "/studies/my-uuid"
    storage_service.create_study.assert_called_once_with("study2", [], PARAMS)


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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)

    result = client.post("/v1/studies")

    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value

    study_data = io.BytesIO(path_zip.read_bytes())
    result = client.post("/v1/studies/_import", files={"study": study_data})

    assert result.json() == "/studies/" + study_name
    assert result.status_code == HTTPStatus.CREATED.value
    mock_storage_service.import_study.assert_called_once()


@pytest.mark.unit_test
def test_copy_study(tmp_path: Path, storage_service_builder) -> None:
    storage_service = Mock()
    storage_service.copy_study.return_value = "/studies/study-copied"

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)

    result = client.post("/v1/studies/existing-study/copy?dest=study-copied")

    storage_service.copy_study.assert_called_with(
        src_uuid="existing-study",
        dest_study_name="study-copied",
        group_ids=[],
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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/v1/studies")

    assert result.json() == studies


def test_study_metadata(tmp_path: str, storage_service_builder) -> None:
    study = {"antares": {"caption": ""}}
    storage_service = Mock()
    storage_service.get_study_information.return_value = study

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/1")

    assert result.json() == study


@pytest.mark.unit_test
def test_server_health() -> None:
    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=Mock(),
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/health", stream=True)
    assert result.json() == {"status": "available"}


@pytest.mark.unit_test
def test_export_files() -> None:
    mock_storage_service = Mock()
    mock_storage_service.export_study.return_value = BytesIO(b"Hello")

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/name/export", stream=True)

    assert result.raw.data == b"Hello"
    mock_storage_service.export_study.assert_called_once_with(
        "name", PARAMS, True
    )


@pytest.mark.unit_test
def test_export_params() -> None:
    mock_storage_service = Mock()
    mock_storage_service.export_study.return_value = BytesIO(b"Hello")

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/name/export", stream=True)

    assert result.raw.data == b"Hello"

    client.get("/v1/studies/name/export?no_output=true")
    client.get("/v1/studies/name/export?no_output=false")
    mock_storage_service.export_study.assert_has_calls(
        [
            call(Markup("name"), PARAMS, False),
            call(Markup("name"), PARAMS, True),
        ]
    )


@pytest.mark.unit_test
def test_delete_study() -> None:
    mock_storage_service = Mock()

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    client.delete("/v1/studies/name")

    mock_storage_service.delete_study.assert_called_once_with("name", PARAMS)


@pytest.mark.unit_test
def test_import_matrix() -> None:
    mock_storage_service = Mock()

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post("/v1/file/" + path, files={"matrix": data})

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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)

    data = io.BytesIO(b"hello")
    path = "path/to/matrix.txt"
    result = client.post(
        "/v1/file/" + path, data={"matrix": (data, "matrix.txt")}
    )

    assert result.status_code == HTTPStatus.NOT_FOUND.value


@pytest.mark.unit_test
def test_edit_study() -> None:
    mock_storage_service = Mock()
    mock_storage_service.edit_study.return_value = {}

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app)
    client.post(
        "/v1/studies/my-uuid/raw?path=url/to/change", json={"Hello": "World"}
    )

    mock_storage_service.edit_study.assert_called_once_with(
        "my-uuid", "url/to/change", {"Hello": "World"}, PARAMS
    )


@pytest.mark.unit_test
def test_edit_study_fail() -> None:
    mock_storage_service = Mock()

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post("/v1/studies/my-uuid/raw?path=url/to/change", json={})

    assert res.status_code == 400

    mock_storage_service.edit_study.assert_not_called()


@pytest.mark.unit_test
def test_validate() -> None:
    mock_service = Mock()
    mock_service.check_errors.return_value = ["Hello"]

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/v1/studies/my-uuid/validate")

    assert res.json() == ["Hello"]
    mock_service.check_errors.assert_called_once_with("my-uuid")


@pytest.mark.unit_test
def test_output_download() -> None:
    mock_service = Mock()

    output_data = MatrixAggregationResult(
        index=MatrixIndex(),
        data={"td3_37_de-38_pl": {"1": {"H. VAL|Euro/MWh": [0.5, 0.6, 0.7]}}},
        warnings=[],
    )
    mock_service.download_outputs.return_value = output_data

    study_download = StudyDownloadDTO(
        type="AREA",
        years=[1],
        level="annual",
        filterIn="",
        filterOut="",
        filter=[],
        columns=["00001|td3_37_de-38_pl|H. VAL|Euro/MWh"],
        synthesis=False,
        includeClusters=True,
    )

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/studies/my-uuid/outputs/my-output-id/download",
        json=study_download.dict(),
    )
    assert res.json() == output_data.dict()


@pytest.mark.unit_test
def test_sim_reference() -> None:
    mock_service = Mock()
    study_id = "my-study-id"
    output_id = "my-output-id"

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.put(f"/v1/studies/{study_id}/outputs/{output_id}/reference")
    mock_service.set_sim_reference.assert_called_once_with(
        study_id, output_id, True, PARAMS
    )
    assert res.json() == "OK"


@pytest.mark.unit_test
def test_sim_result() -> None:
    mock_service = Mock()
    study_id = "my-study-id"
    settings = StudySimSettingsDTO(
        general=dict(),
        input=dict(),
        output=dict(),
        optimization=dict(),
        otherPreferences=dict(),
        advancedParameters=dict(),
        seedsMersenneTwister=dict(),
    )
    result_data = [
        StudySimResultDTO(
            name="output-id",
            type="economy",
            settings=settings,
            completionDate="",
            referenceStatus=True,
            synchronized=False,
            status="",
        )
    ]
    mock_service.get_study_sim_result.return_value = result_data
    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.json() == result_data


@pytest.mark.unit_test
def test_study_permission_management(
    tmp_path: Path, storage_service_builder
) -> None:
    storage_service = Mock()

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        user_service=Mock(),
        matrix_service=Mock(),
        config=CONFIG,
    )
    client = TestClient(app, raise_server_exceptions=False)

    result = client.put("/v1/studies/existing-study/owner/2")
    storage_service.change_owner.assert_called_with(
        "existing-study",
        2,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/v1/studies/existing-study/groups/group-a")
    storage_service.add_group.assert_called_with(
        "existing-study",
        "group-a",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.delete("/v1/studies/existing-study/groups/group-b")
    storage_service.remove_group.assert_called_with(
        "existing-study",
        "group-b",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/v1/studies/existing-study/public_mode/FULL")
    storage_service.set_public_mode.assert_called_with(
        "existing-study",
        PublicMode.FULL,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK.value

    result = client.put("/v1/studies/existing-study/public_mode/UNKNOWN")
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY.value
