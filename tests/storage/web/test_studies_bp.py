import io
import shutil
import uuid
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from antarest.core.config import (
    Config,
    SecurityConfig,
    StorageConfig,
    WorkspaceConfig,
)
from antarest.core.exceptions import UrlNotMatchJsonDataError
from antarest.core.filetransfer.model import (
    FileDownloadDTO,
    FileDownloadTaskDTO,
)
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_REFERENCE_TEMPLATES,
    MatrixAggregationResultDTO,
    MatrixIndex,
    OwnerInfo,
    PublicMode,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    StudyMetadataDTO,
    StudySimResultDTO,
    StudySimSettingsDTO,
    TimeSerie,
    TimeSeriesData,
)
from fastapi import FastAPI
from markupsafe import Markup
from starlette.testclient import TestClient
from tests.storage.conftest import SimpleFileTransferManager

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
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    client.get("/v1/studies/study1/raw?path=settings/general/params")

    mock_service.get.assert_called_once_with(
        "study1", "settings/general/params", 3, True, PARAMS
    )


@pytest.mark.unit_test
def test_404() -> None:
    mock_storage_service = Mock()
    mock_storage_service.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    result = client.get("/v1/studies/study1/raw?path=settings/general/params")
    assert result.status_code == HTTPStatus.NOT_FOUND

    result = client.get("/v1/studies/WRONG_STUDY/raw")
    assert result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit_test
def test_server_with_parameters() -> None:
    mock_storage_service = Mock()
    mock_storage_service.get.return_value = {}

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/study1/raw?depth=4")

    parameters = RequestParameters(user=ADMIN)

    assert result.status_code == HTTPStatus.OK
    mock_storage_service.get.assert_called_once_with(
        "study1", "/", 4, True, parameters
    )

    result = client.get("/v1/studies/study2/raw?depth=WRONG_TYPE")
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    result = client.get("/v1/studies/study2/raw")
    assert result.status_code == HTTPStatus.OK

    excepted_parameters = RequestParameters(user=ADMIN)
    mock_storage_service.get.assert_called_with(
        "study2", "/", 3, True, excepted_parameters
    )


@pytest.mark.unit_test
def test_create_study(tmp_path: str, project_path) -> None:
    path_studies = Path(tmp_path)
    path_study = path_studies / "study1"
    path_study.mkdir()
    (path_study / "study.antares").touch()

    storage_service = Mock()
    storage_service.create_study.return_value = "my-uuid"

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)

    result_right = client.post("/v1/studies?name=study2")

    assert result_right.status_code == HTTPStatus.CREATED
    assert result_right.json() == "my-uuid"
    storage_service.create_study.assert_called_once_with(
        "study2", "", [], PARAMS
    )


@pytest.mark.unit_test
def test_import_study_zipped(tmp_path: Path, project_path) -> None:
    study_name = "study1"
    path_study = tmp_path / study_name
    path_study.mkdir()
    path_file = path_study / "study.antares"
    path_file.write_text("[antares]")

    shutil.make_archive(str(path_study), "zip", path_study)
    path_zip = tmp_path / "study1.zip"

    mock_storage_service = Mock()
    study_uuid = str(uuid.uuid4())
    mock_storage_service.import_study.return_value = study_uuid

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)

    result = client.post("/v1/studies")

    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    study_data = io.BytesIO(path_zip.read_bytes())
    result = client.post("/v1/studies/_import", files={"study": study_data})

    assert result.json() == study_uuid
    assert result.status_code == HTTPStatus.CREATED
    mock_storage_service.import_study.assert_called_once()


@pytest.mark.unit_test
def test_copy_study(tmp_path: Path) -> None:
    storage_service = Mock()
    storage_service.copy_study.return_value = "/studies/study-copied"

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)

    result = client.post("/v1/studies/existing-study/copy?dest=study-copied")

    storage_service.copy_study.assert_called_with(
        src_uuid="existing-study",
        dest_study_name="study-copied",
        group_ids=[],
        with_outputs=False,
        use_task=True,
        params=PARAMS,
    )
    assert result.status_code == HTTPStatus.CREATED


@pytest.mark.unit_test
def test_list_studies(tmp_path: str) -> None:
    studies = {
        "study1": StudyMetadataDTO(
            id="a",
            name="study1",
            version=700,
            created=str(datetime.utcfromtimestamp(0)),
            updated=str(datetime.utcfromtimestamp(0)),
            type="RawStudy",
            owner=OwnerInfo(name="foo"),
            groups=[],
            public_mode=PublicMode.FULL,
            workspace="default",
            managed=True,
            archived=False,
        ),
        "study2": StudyMetadataDTO(
            id="b",
            name="study2",
            version=700,
            created=str(datetime.utcfromtimestamp(0)),
            updated=str(datetime.utcfromtimestamp(0)),
            type="RawStudy",
            owner=OwnerInfo(name="foo"),
            groups=[],
            public_mode=PublicMode.FULL,
            workspace="default",
            managed=True,
            archived=False,
        ),
    }

    storage_service = Mock()
    storage_service.get_studies_information.return_value = studies

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    result = client.get("/v1/studies")

    assert {
        k: StudyMetadataDTO.parse_obj(v) for k, v in result.json().items()
    } == studies


def test_study_metadata(tmp_path: str) -> None:
    study = StudyMetadataDTO(
        id="a",
        name="b",
        version=700,
        created=str(datetime.utcfromtimestamp(0)),
        updated=str(datetime.utcfromtimestamp(0)),
        type="RawStudy",
        owner=OwnerInfo(name="foo"),
        groups=[],
        public_mode=PublicMode.FULL,
        workspace="default",
        managed=True,
        archived=False,
    )
    storage_service = Mock()
    storage_service.get_study_information.return_value = study

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/1")

    assert StudyMetadataDTO.parse_obj(result.json()) == study


@pytest.mark.unit_test
def test_export_files(tmp_path: Path) -> None:
    mock_storage_service = Mock()
    expected = FileDownloadTaskDTO(
        file=FileDownloadDTO(
            id="some id",
            name="name",
            filename="filename",
            expiration_date=None,
            ready=True,
        ),
        task="some-task",
    )
    mock_storage_service.export_study.return_value = expected

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    result = client.get("/v1/studies/name/export", stream=True)

    assert (
        FileDownloadTaskDTO.parse_obj(result.json()).json() == expected.json()
    )
    mock_storage_service.export_study.assert_called_once_with(
        "name", PARAMS, True
    )


@pytest.mark.unit_test
def test_export_params(tmp_path: Path) -> None:
    mock_storage_service = Mock()
    expected = FileDownloadTaskDTO(
        file=FileDownloadDTO(
            id="some id",
            name="name",
            filename="filename",
            expiration_date=None,
            ready=True,
        ),
        task="some-task",
    )
    mock_storage_service.export_study.return_value = expected

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
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
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)

    study_uuid = "8319b5f8-2a35-4984-9ace-2ab072bd6eef"
    client.delete(f"/v1/studies/{study_uuid}")

    mock_storage_service.delete_study.assert_called_once_with(
        study_uuid, False, PARAMS
    )


@pytest.mark.unit_test
def test_edit_study() -> None:
    mock_storage_service = Mock()
    mock_storage_service.edit_study.return_value = {}

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_storage_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app)
    client.post(
        "/v1/studies/my-uuid/raw?path=url/to/change", json={"Hello": "World"}
    )

    mock_storage_service.edit_study.assert_called_once_with(
        "my-uuid", "url/to/change", {"Hello": "World"}, PARAMS
    )


# @pytest.mark.unit_test
# def test_edit_study_fail() -> None:
#     mock_storage_service = Mock()
#
#     app = FastAPI(title=__name__)
#     build_study_service(
#         app,
#         cache=Mock(),
#         task_service=Mock(),
#         file_transfer_manager=Mock(),
#         study_service=mock_storage_service,
#         config=CONFIG,
#         user_service=Mock(),
#         matrix_service=Mock(spec=MatrixService),
#     )
#     client = TestClient(app, raise_server_exceptions=False)
#     res = client.post("/v1/studies/my-uuid/raw?path=url/to/change", json={})
#
#     assert res.status_code == 400
#
#     mock_storage_service.edit_study.assert_not_called()


@pytest.mark.unit_test
def test_validate() -> None:
    mock_service = Mock()
    mock_service.check_errors.return_value = ["Hello"]

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/v1/studies/my-uuid/raw/validate")

    assert res.json() == ["Hello"]
    mock_service.check_errors.assert_called_once_with("my-uuid")


@pytest.mark.unit_test
def test_output_download(tmp_path: Path) -> None:
    mock_service = Mock()

    output_data = MatrixAggregationResultDTO(
        index=MatrixIndex(),
        data=[
            TimeSeriesData(
                name="td3_37_de^38_pl",
                type=StudyDownloadType.LINK,
                data={
                    "1": [
                        TimeSerie(
                            name="H. VAL",
                            unit="Euro/MWh",
                            data=[0.5, 0.6, 0.7],
                        )
                    ]
                },
            )
        ],
        warnings=[],
    )
    mock_service.download_outputs.return_value = output_data

    study_download = StudyDownloadDTO(
        type=StudyDownloadType.AREA,
        years=[1],
        level=StudyDownloadLevelDTO.ANNUAL,
        filterIn="",
        filterOut="",
        filter=[],
        columns=["00001|td3_37_de-38_pl|H. VAL|Euro/MWh"],
        synthesis=False,
        includeClusters=True,
    )

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=SimpleFileTransferManager(
            Config(storage=StorageConfig(tmp_dir=tmp_path))
        ),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/studies/my-uuid/outputs/my-output-id/download",
        json=study_download.dict(),
    )
    assert res.json() == output_data.dict()


@pytest.mark.unit_test
def test_output_whole_download(tmp_path: Path) -> None:
    mock_service = Mock()
    output_id = "my_output_id"

    expected = FileDownloadTaskDTO(
        file=FileDownloadDTO(
            id="some id",
            name="name",
            filename="filename",
            expiration_date=None,
            ready=True,
        ),
        task="some-task",
    )
    mock_service.export_output.return_value = expected

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=SimpleFileTransferManager(
            Config(storage=StorageConfig(tmp_dir=tmp_path))
        ),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get(
        f"/v1/studies/my-uuid/outputs/{output_id}/export",
    )
    assert res.status_code == HTTPStatus.OK


@pytest.mark.unit_test
def test_sim_reference() -> None:
    mock_service = Mock()
    study_id = str(uuid.uuid4())
    output_id = "my-output-id"

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.put(f"/v1/studies/{study_id}/outputs/{output_id}/reference")
    mock_service.set_sim_reference.assert_called_once_with(
        study_id, output_id, True, PARAMS
    )
    assert res.status_code == HTTPStatus.OK
    assert res.json() == ""


@pytest.mark.unit_test
def test_sim_result() -> None:
    mock_service = Mock()
    study_id = str(uuid.uuid4())
    settings = StudySimSettingsDTO(
        general={},
        input={},
        output={},
        optimization={},
        otherPreferences={},
        advancedParameters={},
        seedsMersenneTwister={},
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
            archived=False,
        )
    ]
    mock_service.get_study_sim_result.return_value = result_data
    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=mock_service,
        config=CONFIG,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
    )
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.json() == result_data


@pytest.mark.unit_test
def test_study_permission_management(tmp_path: Path) -> None:
    storage_service = Mock()

    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=storage_service,
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
        config=CONFIG,
    )
    client = TestClient(app, raise_server_exceptions=False)

    result = client.put("/v1/studies/existing-study/owner/2")
    storage_service.change_owner.assert_called_with(
        "existing-study",
        2,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK

    result = client.put("/v1/studies/existing-study/groups/group-a")
    storage_service.add_group.assert_called_with(
        "existing-study",
        "group-a",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK

    result = client.delete("/v1/studies/existing-study/groups/group-b")
    storage_service.remove_group.assert_called_with(
        "existing-study",
        "group-b",
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK

    result = client.put("/v1/studies/existing-study/public_mode/FULL")
    storage_service.set_public_mode.assert_called_with(
        "existing-study",
        PublicMode.FULL,
        PARAMS,
    )
    assert result.status_code == HTTPStatus.OK

    result = client.put("/v1/studies/existing-study/public_mode/UNKNOWN")
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.unit_test
def test_get_study_versions(tmp_path: Path) -> None:
    app = FastAPI(title=__name__)
    build_study_service(
        app,
        cache=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=Mock(),
        user_service=Mock(),
        matrix_service=Mock(spec=MatrixService),
        config=CONFIG,
    )
    client = TestClient(app, raise_server_exceptions=False)

    result = client.get("/v1/studies/_versions")
    assert result.json() == list(STUDY_REFERENCE_TEMPLATES.keys())
