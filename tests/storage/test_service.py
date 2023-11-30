import contextlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Union
from unittest.mock import ANY, Mock, call, patch, seal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.filetransfer.model import FileDownload, FileDownloadTaskDTO
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTGroup, JWTUser
from antarest.core.model import JSON, SUB_JSON, PermissionInfo
from antarest.core.permissions import StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.tasks.model import TaskDTO, TaskStatus, TaskType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, GroupDTO, Role, User
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    ExportFormat,
    MatrixAggregationResultDTO,
    MatrixIndex,
    OwnerInfo,
    PublicMode,
    RawStudy,
    Study,
    StudyAdditionalData,
    StudyContentStatus,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    StudyFolder,
    StudyMetadataDTO,
    TimeSerie,
    TimeSeriesData,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import MAX_MISSING_STUDY_TIMEOUT, StudyService, StudyUpgraderTask, UserHasNotPermissionError
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    DistrictSet,
    FileStudyTreeConfig,
    Link,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import assert_permission, assert_permission_on_studies, study_matcher
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from antarest.worker.archive_worker import ArchiveTaskArgs
from tests.helpers import with_db_context


def build_study_service(
    raw_study_service: RawStudyService,
    repository: StudyMetadataRepository,
    config: Config,
    user_service: LoginService = Mock(),
    cache_service: ICache = Mock(),
    variant_study_service=Mock(),
    task_service=Mock(),
) -> StudyService:
    return StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        user_service=user_service,
        repository=repository,
        event_bus=Mock(),
        task_service=task_service,
        file_transfer_manager=Mock(),
        cache_service=cache_service,
        config=config,
    )


def study_to_dto(study: Study) -> StudyMetadataDTO:
    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=int(study.version),
        created=str(study.created_at),
        updated=str(study.updated_at),
        workspace=DEFAULT_WORKSPACE_NAME,
        managed=True,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=OwnerInfo(id=study.owner.id, name=study.owner.name)
        if study.owner is not None
        else OwnerInfo(name="Unknown"),
        groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=study.additional_data.horizon,
        scenario=None,
        status=None,
        doc=None,
        folder=None,
    )


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_study_listing() -> None:
    bob = User(id=2, name="bob")
    alice = User(id=3, name="alice")

    a = RawStudy(
        id="A",
        owner=bob,
        type="rawstudy",
        name="A",
        version=810,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        path="",
        workspace=DEFAULT_WORKSPACE_NAME,
        additional_data=StudyAdditionalData(),
    )
    b = RawStudy(
        id="B",
        owner=alice,
        type="rawstudy",
        name="B",
        version=810,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        path="",
        workspace="other",
        additional_data=StudyAdditionalData(),
    )
    c = RawStudy(
        id="C",
        owner=bob,
        type="rawstudy",
        name="C",
        version=810,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        path="",
        workspace="other2",
        additional_data=StudyAdditionalData(),
    )

    # Mock
    repository = Mock()
    repository.get_all.return_value = [a, b, c]

    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.get_study_information.side_effect = study_to_dto

    cache = Mock(spec=ICache)
    cache.get.return_value = None

    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(raw_study_service, repository, config, cache_service=cache)

    studies = service.get_studies_information(
        managed=False,
        name=None,
        workspace=None,
        folder=None,
        params=RequestParameters(user=JWTUser(id=2, impersonator=2, type="users")),
    )

    expected_result = {e.id: e for e in map(lambda x: study_to_dto(x), [a, c])}
    assert expected_result == studies
    cache.get.return_value = {e.id: e for e in map(lambda x: study_to_dto(x), [a, b, c])}

    studies = service.get_studies_information(
        managed=False,
        name=None,
        workspace=None,
        folder=None,
        params=RequestParameters(user=JWTUser(id=2, impersonator=2, type="users")),
    )

    assert expected_result == studies
    cache.put.assert_called_once()

    cache.get.return_value = None
    studies = service.get_studies_information(
        managed=True,
        name=None,
        workspace=None,
        folder=None,
        params=RequestParameters(user=JWTUser(id=2, impersonator=2, type="users")),
    )

    expected_result = {e.id: e for e in map(lambda x: study_to_dto(x), [a])}
    assert expected_result == studies


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_sync_studies_from_disk() -> None:
    now = datetime.utcnow()
    ma = RawStudy(id="a", path="a")
    fa = StudyFolder(path=Path("a"), workspace="", groups=[])
    mb = RawStudy(id="b", path="b")
    mc = RawStudy(
        id="c",
        path="c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=0),
    )
    md = RawStudy(
        id="d",
        path="d",
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT + 1),
    )
    me = RawStudy(
        id="e",
        path="e",
        created_at=now,
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT - 1),
    )
    fc = StudyFolder(path=Path("c"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])
    fe = StudyFolder(path=Path("e"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])
    ff = StudyFolder(path=Path("f"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])

    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, md, me]]
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config)

    service.sync_studies_on_disk([fa, fc, fe, ff])

    repository.delete.assert_called_once_with(md.id)
    repository.save.assert_has_calls(
        [
            call(RawStudy(id="b", path="b", missing=ANY)),
            call(RawStudy(id="e", path="e", created_at=now, missing=None)),
            call(
                RawStudy(
                    id=ANY,
                    path="f",
                    workspace=DEFAULT_WORKSPACE_NAME,
                    name="f",
                    folder="f",
                    public_mode=PublicMode.FULL,
                )
            ),
        ]
    )


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_partial_sync_studies_from_disk() -> None:
    now = datetime.utcnow()
    ma = RawStudy(id="a", path="a")
    mb = RawStudy(id="b", path="b")
    mc = RawStudy(
        id="c",
        path=f"directory{os.sep}c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=0),
    )
    md = RawStudy(
        id="d",
        path=f"directory{os.sep}d",
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT + 1),
    )
    me = RawStudy(
        id="e",
        path=f"directory{os.sep}e",
        created_at=now,
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT - 1),
    )
    fc = StudyFolder(path=Path("directory/c"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])
    fe = StudyFolder(path=Path("directory/e"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])
    ff = StudyFolder(path=Path("directory/f"), workspace=DEFAULT_WORKSPACE_NAME, groups=[])

    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, md, me]]
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config)

    service.sync_studies_on_disk([fc, fe, ff], directory=Path("directory"))

    repository.delete.assert_called_once_with(md.id)
    repository.save.assert_called_with(
        RawStudy(
            id=ANY,
            path=f"directory{os.sep}f",
            name="f",
            folder=f"directory{os.sep}f",
            created_at=ANY,
            missing=None,
            public_mode=PublicMode.FULL,
            workspace=DEFAULT_WORKSPACE_NAME,
        )
    )


@pytest.mark.unit_test
def test_remove_duplicate() -> None:
    ma = RawStudy(id="a", path="a")
    mb = RawStudy(id="b", path="a")

    repository = Mock()
    repository.get_all.return_value = [ma, mb]
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config)

    service.remove_duplicates()
    repository.delete.assert_called_once_with(mb.id)


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_create_study() -> None:
    # Mock
    repository = Mock()

    # Input
    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    expected = RawStudy(
        id=str(uuid4()),
        name="new-study",
        version="VERSION",
        author="AUTHOR",
        created_at=datetime.utcfromtimestamp(1234),
        updated_at=datetime.utcfromtimestamp(9876),
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )

    user_service = Mock()
    user_service.get_user.return_value = user

    study_service = Mock()
    study_service.get_default_workspace_path.return_value = Path("")
    study_service.get_study_information.return_value = {
        "antares": {
            "caption": "CAPTION",
            "version": "VERSION",
            "author": "AUTHOR",
            "created": 1234,
            "lastsave": 9876,
        }
    }
    study_service.create.return_value = expected
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config, user_service=user_service)

    with pytest.raises(UserHasNotPermissionError):
        service.create_study(
            "new-study",
            "720",
            ["my-group"],
            RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
        )

    service.create_study(
        "new-study",
        "720",
        ["my-group"],
        RequestParameters(
            JWTUser(
                id=0,
                impersonator=0,
                type="users",
                groups=[JWTGroup(id="my-group", name="group", role=RoleType.WRITER)],
            )
        ),
    )

    study_service.create.assert_called()
    repository.save.assert_called_once_with(expected)


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_save_metadata() -> None:
    # Mock
    repository = Mock()

    uuid = str(uuid4())

    study_service = Mock()
    study_service.get_study_information.return_value = {
        "antares": {
            "caption": "CAPTION",
            "version": "VERSION",
            "author": "AUTHOR",
            "created": 1234,
            "lastsave": 9876,
        }
    }

    # Input
    jwt = JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="my-group", name="group", role=RoleType.ADMIN)],
    )
    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    # Expected
    study = RawStudy(
        id=uuid,
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config)

    service.user_service.get_user.return_value = user
    service._save_study(
        RawStudy(id=uuid, workspace=DEFAULT_WORKSPACE_NAME),
        owner=jwt,
    )
    repository.save.assert_called_once_with(study)


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_download_output() -> None:
    study_service = Mock()
    repository = Mock()

    input_study = RawStudy(
        id="c",
        path="c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=0),
    )
    input_data = StudyDownloadDTO(
        type="AREA",
        years=[],
        level="annual",
        filterIn="",
        filterOut="",
        filter=[],
        columns=[],
        synthesis=False,
        includeClusters=True,
    )

    area = Area(
        name="area",
        links={"west": Link(filters_synthesis=[], filters_year=[])},
        thermals=[],
        renewables=[],
        filters_synthesis=[],
        filters_year=[],
    )

    sim = Simulation(
        name="",
        date="",
        mode="",
        nbyears=1,
        synthesis=True,
        by_year=True,
        error=False,
        playlist=[0],
        xpansion="",
    )
    file_config = FileStudyTreeConfig(
        study_path=input_study.path,
        path=input_study.path,
        study_id="",
        version=-1,
        areas={"east": area},
        sets={"north": DistrictSet()},
        outputs={"output-id": sim},
        store_new_set=False,
    )
    study = Mock()

    repository.get.return_value = input_study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config)

    res_study = {"columns": [["H. VAL", "Euro/MWh"]], "data": [[0.5]]}
    res_study_details = {
        "columns": [["some cluster", "Euro/MWh"]],
        "data": [[0.8]],
    }
    study_service.get_raw.return_value = FileStudy(config=file_config, tree=study)
    output_config = {
        "general": {
            "first-month-in-year": "january",
            "january.1st": "Monday",
            "leapyear": False,
            "first.weekday": "Monday",
            "simulation.start": 1,
            "simulation.end": 354,
        }
    }
    study.get.side_effect = [
        output_config,
        res_study,
        res_study_details,
        output_config,
        res_study,
        output_config,
        res_study,
        res_study_details,
    ]

    # AREA TYPE
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2001-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east",
                type=StudyDownloadType.AREA,
                data={
                    1: [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5]),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=[0.8]),
                    ]
                },
            )
        ],
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        use_task=False,
        filetype=ExportFormat.JSON,
        params=RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert MatrixAggregationResultDTO.parse_raw(result.body) == res_matrix

    # AREA TYPE - ZIP & TASK
    export_file_download = FileDownload(
        id="download-id",
        filename="filename",
        name="name",
        ready=False,
        path="path",
        owner=None,
        expiration_date=datetime.utcnow(),
    )
    service.file_transfer_manager.request_download.return_value = export_file_download
    task_id = "task-id"
    service.task_service.add_task.return_value = task_id

    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        use_task=True,
        filetype=ExportFormat.ZIP,
        params=RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )

    res_file_download = FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)
    assert result == res_file_download

    # LINK TYPE
    input_data.type = StudyDownloadType.LINK
    input_data.filter = ["east>west"]
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2001-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east^west",
                type=StudyDownloadType.LINK,
                data={1: [TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5])]},
            )
        ],
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        use_task=False,
        filetype=ExportFormat.JSON,
        params=RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert MatrixAggregationResultDTO.parse_raw(result.body) == res_matrix

    # CLUSTER TYPE
    input_data.type = StudyDownloadType.DISTRICT
    input_data.filter = []
    input_data.filterIn = "n"
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2001-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="north",
                type=StudyDownloadType.DISTRICT,
                data={
                    1: [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5]),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=[0.8]),
                    ]
                },
            )
        ],
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        use_task=False,
        filetype=ExportFormat.JSON,
        params=RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert MatrixAggregationResultDTO.parse_raw(result.body) == res_matrix


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_change_owner() -> None:
    uuid = str(uuid4())
    alice = User(id=2)
    bob = User(id=3, name="Bob")

    mock_file_study = Mock()
    mock_file_study.tree.get_node.return_value = Mock(spec=IniFileNode)

    repository = Mock()
    user_service = Mock()
    study_service = Mock(spec=RawStudyService)
    study_service.get_raw.return_value = mock_file_study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config, user_service=user_service)
    service.storage_service.variant_study_service.command_factory.command_context = Mock(spec=CommandContext)

    study = RawStudy(id=uuid, owner=alice)
    repository.get.return_value = study
    user_service.get_user.return_value = bob
    service._edit_study_using_command = Mock()

    service.change_owner(uuid, 2, RequestParameters(JWTUser(id=2, impersonator=2, type="users")))
    user_service.get_user.assert_called_once_with(2, RequestParameters(JWTUser(id=2, impersonator=2, type="users")))
    repository.save.assert_called_with(RawStudy(id=uuid, owner=bob, last_access=ANY))
    repository.save.assert_called_with(RawStudy(id=uuid, owner=bob))

    service._edit_study_using_command.assert_called_once_with(study=study, url="study/antares/author", data="Bob")

    with pytest.raises(UserHasNotPermissionError):
        service.change_owner(
            uuid,
            1,
            RequestParameters(JWTUser(id=2, impersonator=2, type="users")),
        )


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_manage_group() -> None:
    uuid = str(uuid4())
    alice = User(id=1)
    group_a = Group(id="a", name="Group A")
    group_b = Group(id="b", name="Group B")
    group_a_admin = JWTGroup(id="a", name="Group A", role=RoleType.ADMIN)

    repository = Mock()
    user_service = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config, user_service=user_service)

    repository.get.return_value = Study(id=uuid, owner=alice, groups=[group_a])

    with pytest.raises(UserHasNotPermissionError):
        service.add_group(
            uuid,
            "b",
            RequestParameters(JWTUser(id=2, impersonator=2, type="users")),
        )

    user_service.get_group.return_value = group_b
    service.add_group(
        uuid,
        "b",
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])),
    )

    user_service.get_group.assert_called_once_with(
        "b",
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])),
    )
    repository.save.assert_called_with(Study(id=uuid, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = Study(id=uuid, owner=alice, groups=[group_a, group_b])
    service.add_group(
        uuid,
        "b",
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])),
    )
    user_service.get_group.assert_called_with(
        "b",
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])),
    )
    repository.save.assert_called_with(Study(id=uuid, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = Study(id=uuid, owner=alice, groups=[group_a, group_b])
    service.remove_group(
        uuid,
        "a",
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])),
    )
    repository.save.assert_called_with(Study(id=uuid, owner=alice, groups=[group_b]))


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_set_public_mode() -> None:
    uuid = str(uuid4())
    group_admin = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)

    repository = Mock()
    user_service = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config, user_service=user_service)

    repository.get.return_value = Study(id=uuid)

    with pytest.raises(UserHasNotPermissionError):
        service.set_public_mode(
            uuid,
            PublicMode.FULL,
            RequestParameters(JWTUser(id=2, impersonator=2, type="users")),
        )

    service.set_public_mode(
        uuid,
        PublicMode.FULL,
        RequestParameters(JWTUser(id=2, impersonator=2, type="users", groups=[group_admin])),
    )
    repository.save.assert_called_with(Study(id=uuid, public_mode=PublicMode.FULL))


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_check_errors():
    study_service = Mock()
    study_service.check_errors.return_value = ["Hello", "World"]

    study = RawStudy(id="hello world")
    repo = Mock()
    repo.get.return_value = study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repo, config)

    assert ["Hello", "World"] == service.check_errors("hello world")
    study_service.check_errors.assert_called_once_with(study)
    repo.get.assert_called_once_with("hello world")


@pytest.mark.unit_test
def test_study_match() -> None:
    assert not study_matcher(name=None, folder="ab", workspace="hell")(
        StudyMetadataDTO.construct(id="1", folder="abc/de", workspace="hello")
    )
    assert study_matcher(name=None, folder="ab", workspace="hello")(
        StudyMetadataDTO.construct(id="1", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name=None, folder="abd", workspace="hello")(
        StudyMetadataDTO.construct(id="1", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name=None, folder="ab", workspace="hello")(
        StudyMetadataDTO.construct(id="1", workspace="hello")
    )
    assert study_matcher(name="f", folder=None, workspace="hello")(
        StudyMetadataDTO.construct(id="1", name="foo", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name="foob", folder=None, workspace="hell")(
        StudyMetadataDTO.construct(id="1", name="foo", folder="abc/de", workspace="hello")
    )


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_assert_permission() -> None:
    uuid = str(uuid4())
    admin_group = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
    admin = JWTUser(id=1, impersonator=1, type="users", groups=[admin_group])
    group = JWTGroup(id="my-group", name="g", role=RoleType.ADMIN)
    jwt = JWTUser(id=0, impersonator=0, type="users", groups=[group])
    group_2 = JWTGroup(id="my-group-2", name="g2", role=RoleType.RUNNER)
    jwt_2 = JWTUser(id=3, impersonator=3, type="users", groups=[group_2])
    good = User(id=0)
    wrong = User(id=2)

    repository = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config)

    # wrong owner
    repository.get.return_value = Study(id=uuid, owner=wrong)
    study = service.get_study(uuid)
    with pytest.raises(UserHasNotPermissionError):
        assert_permission(jwt, study, StudyPermissionType.READ)
    assert not assert_permission(jwt, study, StudyPermissionType.READ, raising=False)

    # good owner
    study = Study(id=uuid, owner=good)
    assert assert_permission(jwt, study, StudyPermissionType.MANAGE_PERMISSIONS)

    # wrong group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        assert_permission(jwt, study, StudyPermissionType.READ)
    assert not assert_permission(jwt, study, StudyPermissionType.READ, raising=False)

    # good group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="my-group")])
    assert assert_permission(jwt, study, StudyPermissionType.MANAGE_PERMISSIONS)

    # super admin can do whatever he wants..
    study = Study(id=uuid)
    assert assert_permission(admin, study, StudyPermissionType.MANAGE_PERMISSIONS)

    # when study found in workspace without group
    study = Study(id=uuid, public_mode=PublicMode.FULL)
    assert not assert_permission(jwt, study, StudyPermissionType.MANAGE_PERMISSIONS, raising=False)
    assert assert_permission(jwt, study, StudyPermissionType.READ)
    assert assert_permission(jwt, study, StudyPermissionType.WRITE)
    assert assert_permission(jwt, study, StudyPermissionType.RUN)

    # some group roles
    study = Study(id=uuid, owner=wrong, groups=[Group(id="my-group-2")])
    assert not assert_permission(jwt_2, study, StudyPermissionType.WRITE, raising=False)
    assert assert_permission(jwt_2, study, StudyPermissionType.READ)


def test_assert_permission_on_studies(db_session: Session) -> None:
    # Given the following user groups :
    user_groups = [
        {
            "name": "admin",
            "role": RoleType.ADMIN,
            "users": ["admin"],
        },
        {
            "name": "Writers",
            "role": RoleType.WRITER,
            "users": ["John", "Jane", "Jack"],
        },
        {
            "name": "Readers",
            "role": RoleType.READER,
            "users": ["Rita", "Ralph"],
        },
    ]

    # Create the JWTGroup and JWTUser objects
    jwt_groups = {}
    jwt_users = {}
    users_sequence = 2  # first non-admin user ID
    for group in user_groups:
        group_name = group["name"]
        jwt_groups[group_name] = JWTGroup(id=group_name, name=group_name, role=group["role"])
        for user_name in group["users"]:
            if user_name == "admin":
                user_id = 1
            else:
                user_id = users_sequence
                users_sequence += 1
            jwt_users[user_name] = JWTUser(
                id=user_id,
                impersonator=user_id,
                type="users",
                groups=[jwt_groups[group_name]],
            )

    # Create the users and groups in the database
    with db_session:
        for group_name, jwt_group in jwt_groups.items():
            db_session.add(Group(id=jwt_group.id, name=group_name))
        for user_name, jwt_user in jwt_users.items():
            db_session.add(User(id=jwt_user.id, name=user_name))
        db_session.commit()

        for user in db_session.query(User):
            user_jwt_groups = jwt_users[user.name].groups
            for user_jwt_group in user_jwt_groups:
                db_session.add(Role(type=user_jwt_group.role, identity_id=user.id, group_id=user_jwt_group.id))
        db_session.commit()

    # John creates a main study and Jane creates two variant studies.
    # They all belong to the same group.
    writers = db_session.query(Group).filter(Group.name == "Writers").one()
    studies = [
        Study(id=uuid4(), name="Main Study", owner_id=jwt_users["John"].id, groups=[writers]),
        Study(id=uuid4(), name="Variant Study 1", owner_id=jwt_users["Jane"].id, groups=[writers]),
        Study(id=uuid4(), name="Variant Study 2", owner_id=jwt_users["Jane"].id, groups=[writers]),
    ]

    # All admin and writers should have WRITE access to the studies.
    # Other members of the group should have no access.
    for user_name, jwt_user in jwt_users.items():
        has_access = any(jwt_group.name in {"admin", "Writers"} for jwt_group in jwt_user.groups)
        actual = assert_permission_on_studies(jwt_user, studies, StudyPermissionType.WRITE, raising=False)
        assert actual == has_access

    # Jack creates a additional variant study and adds it to the readers and writers groups.
    readers = db_session.query(Group).filter(Group.name == "Readers").one()
    studies.append(Study(id=uuid4(), name="Variant Study 3", owner_id=jwt_users["Jack"].id, groups=[readers, writers]))

    # All admin and writers should have READ access to the studies.
    # Other members of the group should have no access, because they don't have access to the writers-only studies.
    for user_name, jwt_user in jwt_users.items():
        has_access = any(jwt_group.name in {"admin", "Writers"} for jwt_group in jwt_user.groups)
        actual = assert_permission_on_studies(jwt_user, studies, StudyPermissionType.READ, raising=False)
        assert actual == has_access

    # Everybody should have access to the last study, because it is in the readers and writers group.
    for user_name, jwt_user in jwt_users.items():
        actual = assert_permission_on_studies(jwt_user, studies[-1:], StudyPermissionType.READ, raising=False)
        assert actual


@pytest.mark.unit_test
def test_delete_study_calls_callback(tmp_path: Path):
    study_uuid = "my_study"
    repository_mock = Mock()
    study_path = tmp_path / study_uuid
    study_path.mkdir()
    (study_path / "study.antares").touch()
    repository_mock.get.return_value = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        path=study_path,
        groups=[],
        owner=None,
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
    )
    service = build_study_service(Mock(), repository_mock, Mock())
    callback = Mock()
    service.add_on_deletion_callback(callback)
    service.storage_service.variant_study_service.has_children.return_value = False

    service.delete_study(
        study_uuid,
        children=False,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    callback.assert_called_once_with(study_uuid)


@pytest.mark.unit_test
def test_delete_with_prefetch(tmp_path: Path):
    study_uuid = "my_study"

    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(Config(), Mock(), Mock(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(),
        Mock(),
        raw_study_service,
        Mock(),
        Mock(),
        Mock(),
        variant_study_repository,
        Mock(),
        Mock(),
    )
    # noinspection PyArgumentList
    service = build_study_service(
        raw_study_service,
        study_metadata_repository,
        Mock(),
        variant_study_service=variant_study_service,
    )

    study_path = tmp_path / study_uuid
    study_path.mkdir()
    (study_path / "study.antares").touch()
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        path=study_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
        last_access=datetime.utcnow(),
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    study_metadata_repository.get.return_value = study_mock
    variant_study_repository.get_children.return_value = []

    # if this fails, it may means the study metadata mock is missing some attribute definition
    # this test is here to prevent errors if we add attribute fetching from child classes (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
        children=False,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    # test for variant studies
    study_mock = Mock(
        spec=VariantStudy,
        archived=False,
        id="my_study",
        path=study_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        last_access=datetime.utcnow(),
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    study_metadata_repository.get.return_value = study_mock
    variant_study_repository.get_children.return_value = []

    # if this fails, it may means the study metadata mock is missing some definition
    # this test is here to prevent errors if we add attribute fetching from child classes (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
        children=False,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


# noinspection PyArgumentList
def test_delete_recursively(tmp_path: Path):
    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(Config(), Mock(), Mock(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(),
        Mock(),
        raw_study_service,
        Mock(),
        Mock(),
        Mock(),
        variant_study_repository,
        Mock(),
        Mock(),
    )
    service = build_study_service(
        raw_study_service,
        study_metadata_repository,
        Mock(),
        variant_study_service=variant_study_service,
    )

    def create_study_fs_mock(variant: bool = False) -> str:
        study_uuid = str(uuid4())
        study_path = tmp_path / study_uuid
        study_path.mkdir()
        study_data = study_path
        if variant:
            study_data = study_path / "snapshot"
            study_data.mkdir()
        (study_data / "study.antares").touch()
        return str(study_path)

    study_path = create_study_fs_mock()
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        path=study_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
        last_access=datetime.utcnow(),
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    v1 = VariantStudy(id="variant_1", path=create_study_fs_mock(variant=True))
    v2 = VariantStudy(id="variant_2", path=create_study_fs_mock(variant=True))
    v3 = VariantStudy(id="sub_variant_1", path=create_study_fs_mock(variant=True))

    study_metadata_repository.get.side_effect = [study_mock, v3, v1, v2]
    variant_study_repository.get_children.side_effect = [
        [
            v1,
            v2,
        ],
        [v3],
        [],
        [],
        [],
        [],
        [],
    ]
    variant_study_repository.get.side_effect = [
        VariantStudy(id="variant_1"),
        VariantStudy(id="sub_variant_1"),
        VariantStudy(id="variant_2"),
    ]

    service.delete_study(
        "my_study",
        children=True,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


@pytest.mark.unit_test
def test_edit_study_with_command():
    study_id = "study_id"

    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )
    command = Mock()
    service._create_edit_study_command = Mock(return_value=command)
    file_study = Mock()
    file_study.config.study_id = study_id
    study_service = Mock(spec=RawStudyService)
    study_service.get_raw.return_value = file_study
    service.storage_service.get_storage = Mock(return_value=study_service)

    service._edit_study_using_command(study=Mock(), url="", data=[])
    command.apply.assert_called_with(file_study)

    study_service = Mock(spec=VariantStudyService)
    study_service.get_raw.return_value = file_study
    service.storage_service.get_storage = Mock(return_value=study_service)
    service._edit_study_using_command(study=Mock(), url="", data=[])

    study_service.append_command.assert_called_once_with(
        study_id=study_id,
        command=command.to_dto(),
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "tree_node,url,data,expected_name",
    [
        (Mock(spec=IniFileNode), "url", 0, "update_config"),
        (Mock(spec=InputSeriesMatrix), "url", [[0]], "replace_matrix"),
        (Mock(spec=RawFileNode), "comments", "0", "update_comments"),
    ],
)
def test_create_command(
    tree_node: INode[JSON, Union[str, int, bool, float, bytes, JSON], JSON],
    url: str,
    data: SUB_JSON,
    expected_name: str,
):
    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )

    matrix_service = Mock(spec=MatrixService)
    matrix_service.create.return_value = "matrix_id"
    command_context = CommandContext(
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        matrix_service=matrix_service,
        patch_service=Mock(spec=PatchService),
    )

    service.storage_service.variant_study_service.command_factory.command_context = command_context

    command = service._create_edit_study_command(tree_node=tree_node, url=url, data=data)

    assert command.command_name.value == expected_name


def test_unarchive_output(tmp_path: Path):
    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )

    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        name="my_study",
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )
    study_mock.name = "my_study"
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}
    service.task_service.reset_mock()
    service.repository.get.return_value = study_mock

    study_id = "my_study"
    output_id = "some-output"
    service.task_service.add_worker_task.return_value = None
    service.task_service.list_tasks.return_value = []
    service.unarchive_output(
        study_id,
        output_id,
        keep_src_zip=True,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    service.task_service.add_worker_task.assert_called_once_with(
        TaskType.UNARCHIVE,
        "unarchive_other_workspace",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_id}.zip"),
            dest=str(tmp_path / "output" / output_id),
            remove_src=False,
        ).dict(),
        name=f"Unarchive output my_study/{output_id} ({study_id})",
        ref_id="my_study",
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Unarchive output my_study/{output_id} ({study_id})",
        task_type=TaskType.UNARCHIVE,
        ref_id=study_id,
        custom_event_messages=None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


def test_archive_output_locks(tmp_path: Path):
    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )

    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        name="my_study",
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )
    study_mock.name = "my_study"
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}
    service.task_service.reset_mock()
    service.repository.get.return_value = study_mock

    study_id = "my_study"
    study_name = study_id
    output_id = "some-output"
    service.task_service.add_worker_task.return_value = None
    service.task_service.list_tasks.side_effect = [
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_id}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_id} ({study_id})",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_id}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_id} ({study_id})",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [],
    ]

    with pytest.raises(TaskAlreadyRunning):
        service.unarchive_output(
            study_id,
            output_id,
            keep_src_zip=True,
            params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    with pytest.raises(TaskAlreadyRunning):
        service.unarchive_output(
            study_id,
            output_id,
            keep_src_zip=True,
            params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    with pytest.raises(TaskAlreadyRunning):
        service.archive_output(
            study_id,
            output_id,
            params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    with pytest.raises(TaskAlreadyRunning):
        service.archive_output(
            study_id,
            output_id,
            params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    service.unarchive_output(
        study_id,
        output_id,
        keep_src_zip=True,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    service.task_service.add_worker_task.assert_called_once_with(
        TaskType.UNARCHIVE,
        "unarchive_other_workspace",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_id}.zip"),
            dest=str(tmp_path / "output" / output_id),
            remove_src=False,
        ).dict(),
        name=f"Unarchive output my_study/{output_id} ({study_id})",
        ref_id="my_study",
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )
    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Unarchive output my_study/{output_id} ({study_id})",
        task_type=TaskType.UNARCHIVE,
        ref_id=study_id,
        custom_event_messages=None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


def test_get_save_logs(tmp_path: Path):
    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )

    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        name="my_study",
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )

    study_mock.name = "my_study"
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}
    service.repository.get.return_value = study_mock
    file_study_config = FileStudyTreeConfig(tmp_path, tmp_path, "study_id", 0, zip_path=None)
    output_config = Mock()
    file_study_config.outputs = {"output_id": output_config}
    output_config.get_file.return_value = "output_id"
    output_config.archived = False
    context = Mock()
    context.resolver.resolve.return_value = None
    service.storage_service.raw_study_service.get_raw.return_value = FileStudy(
        config=file_study_config,
        tree=FileStudyTree(context, file_study_config),
    )

    output_path = tmp_path / "output"
    output_path.mkdir()
    (output_path / "output_id").mkdir()
    (output_path / "logs").mkdir()

    assert (
        service.get_logs(
            "my_study",
            "output_id",
            "job_id",
            True,
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        == ""
    )

    (output_path / "output_id" / "antares-out.log").write_text("some log 2")
    assert (
        service.get_logs(
            "my_study",
            "output_id",
            "job_id",
            False,
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        == "some log 2"
    )

    service.save_logs("my_study", "job_id", "out.log", "some log")

    assert (
        service.get_logs(
            "my_study",
            "output_id",
            "job_id",
            False,
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        == "some log"
    )

    service.save_logs("my_study", "job_id", "err.log", "some log 3")

    assert (
        service.get_logs(
            "my_study",
            "output_id",
            "job_id",
            True,
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        == "some log 3"
    )


def test_task_upgrade_study(tmp_path: Path):
    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )

    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id="my_study",
        name="my_study",
        path=tmp_path,
        version="720",
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )
    study_mock.name = "my_study"
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}
    service.repository.get.return_value = study_mock

    study_id = "my_study"
    service.task_service.reset_mock()
    service.task_service.list_tasks.side_effect = [
        [
            TaskDTO(
                id="1",
                name=f"Upgrade study my_study ({study_id}) to version 800",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [],
    ]

    with pytest.raises(TaskAlreadyRunning):
        service.upgrade_study(
            study_id,
            target_version="",
            params=RequestParameters(user=DEFAULT_ADMIN_USER),
        )

    service.upgrade_study(
        study_id,
        target_version="",
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Upgrade study my_study ({study_id}) to version 800",
        task_type=TaskType.UPGRADE_STUDY,
        ref_id=study_id,
        custom_event_messages=None,
        request_params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )


@with_db_context
@patch("antarest.study.service.upgrade_study")
@pytest.mark.parametrize("workspace", ["other_workspace", DEFAULT_WORKSPACE_NAME])
def test_upgrade_study__raw_study__nominal(
    upgrade_study_mock: Mock,
    tmp_path: Path,
    workspace: str,
):
    study_id = str(uuid.uuid4())
    study_name = "my_study"
    target_version = "800"
    current_version = "720"
    (tmp_path / "study.antares").touch()
    (tmp_path / "study.antares").write_text(f"version = {current_version}")

    # Prepare a RAW study
    # noinspection PyArgumentList
    raw_study = RawStudy(
        id=study_id,
        name=study_name,
        workspace=workspace,
        path=str(tmp_path),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version=current_version,
        additional_data=StudyAdditionalData(),
        archived=False,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
    )

    # Make sure the session is closed to avoid reusing DB objects
    with contextlib.closing(db.session):
        db.session.add(raw_study)
        db.session.commit()

    # The `ICache` is used to invalidate the cache of the study with `invalidate_all`
    cache_service = Mock()

    # The `StudyMetadataRepository` is used to store the study in database.
    repository = StudyMetadataRepository(cache_service)

    # The `StudyStorageService` is used to retrieve:
    # - the `RawStudyService` of a RAW study, or
    # - the `VariantStudyService` of a variant study.
    # It is used to `denormalize`/`normalize` the study.
    # For a variant study, the  `clear_snapshot` is also called
    storage_service = Mock()

    # The `IEventBus` service is used to send event notifications.
    # An event of type `STUDY_EDITED` must be pushed when the upgrade is done.
    event_bus = Mock()

    # Prepare the task for an upgrade
    task = StudyUpgraderTask(
        study_id,
        target_version,
        repository=repository,
        storage_service=storage_service,
        cache_service=cache_service,
        event_bus=event_bus,
    )

    # The task is called with a `TaskUpdateNotifier` a parameter.
    # Some messages could be emitted using the notifier (not a requirement).
    notifier = Mock()
    actual = task(notifier)

    # The `upgrade_study()` function must be called with the right parameters
    upgrade_study_mock.assert_called_with(tmp_path, target_version)

    # The study must be updated in the database
    actual_study: RawStudy = db.session.query(Study).get(study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == target_version

    # An event of type `STUDY_EDITED` must be pushed when the upgrade is done.
    event = Event(
        type=EventType.STUDY_EDITED,
        payload={"id": study_id, "name": study_name},
        permissions=PermissionInfo(
            owner=None,
            groups=[],
            public_mode=PublicMode.NONE,
        ),
    )
    event_bus.push.assert_called_once_with(event)

    # The function must return a successful result
    assert actual.success
    assert study_id in actual.message, f"{actual.message=}"
    assert target_version in actual.message, f"{actual.message=}"


@with_db_context
@patch("antarest.study.service.upgrade_study")
def test_upgrade_study__variant_study__nominal(
    upgrade_study_mock: Mock,
    tmp_path: Path,
):
    study_id = str(uuid.uuid4())
    study_name = "my_study"
    target_version = "800"

    # Prepare a RAW study
    # noinspection PyArgumentList
    variant_study = VariantStudy(
        id=study_id,
        name=study_name,
        path=str(tmp_path),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version="720",
        additional_data=StudyAdditionalData(),
        archived=False,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
    )

    # Make sure the session is closed to avoid reusing DB objects
    with contextlib.closing(db.session):
        db.session.add(variant_study)
        db.session.commit()

    # The `ICache` is used to invalidate the cache of the study with `invalidate_all`
    cache_service = Mock()

    # The `StudyMetadataRepository` is used to store the study in database.
    repository = StudyMetadataRepository(cache_service)

    # The `StudyStorageService` is used to retrieve:
    # - the `RawStudyService` of a RAW study, or
    # - the `VariantStudyService` of a variant study.
    # It is used to `denormalize`/`normalize` the study.
    # For a variant study, the  `clear_snapshot` is also called
    storage_service = Mock()

    # The `IEventBus` service is used to send event notifications.
    # An event of type `STUDY_EDITED` must be pushed when the upgrade is done.
    event_bus = Mock()

    # Prepare the task for an upgrade
    task = StudyUpgraderTask(
        study_id,
        target_version,
        repository=repository,
        storage_service=storage_service,
        cache_service=cache_service,
        event_bus=event_bus,
    )

    # The task is called with a `TaskUpdateNotifier` a parameter.
    # Some messages could be emitted using the notifier (not a requirement).
    notifier = Mock()
    actual = task(notifier)

    # The `upgrade_study()` function is not called for a variant study.
    upgrade_study_mock.assert_not_called()

    # The study must be updated in the database
    actual_study: RawStudy = db.session.query(Study).get(study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == target_version

    # An event of type `STUDY_EDITED` must be pushed when the upgrade is done.
    event = Event(
        type=EventType.STUDY_EDITED,
        payload={"id": study_id, "name": study_name},
        permissions=PermissionInfo(
            owner=None,
            groups=[],
            public_mode=PublicMode.NONE,
        ),
    )
    event_bus.push.assert_called_once_with(event)

    # The function must return a successful result
    assert actual.success
    assert study_id in actual.message, f"{actual.message=}"
    assert target_version in actual.message, f"{actual.message=}"


@with_db_context
@patch("antarest.study.service.upgrade_study")
def test_upgrade_study__raw_study__failed(upgrade_study_mock: Mock, tmp_path: Path):
    study_id = str(uuid.uuid4())
    study_name = "my_study"
    target_version = "800"
    old_version = "720"
    (tmp_path / "study.antares").touch()
    (tmp_path / "study.antares").write_text(f"version = {old_version}")

    # Prepare a RAW study
    # noinspection PyArgumentList
    raw_study = RawStudy(
        id=study_id,
        name=study_name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version=old_version,
        additional_data=StudyAdditionalData(),
        archived=False,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
    )

    # Make sure the session is closed to avoid reusing DB objects
    with contextlib.closing(db.session):
        db.session.add(raw_study)
        db.session.commit()

    # The `ICache` is used to invalidate the cache of the study with `invalidate_all`
    cache_service = Mock()

    # The `StudyMetadataRepository` is used to store the study in database.
    repository = StudyMetadataRepository(cache_service)

    # The `StudyStorageService` is used to retrieve:
    # - the `RawStudyService` of a RAW study, or
    # - the `VariantStudyService` of a variant study.
    # It is used to `denormalize`/`normalize` the study.
    # For a variant study, the  `clear_snapshot` is also called
    storage_service = Mock()

    # The `IEventBus` service is used to send event notifications.
    # An event of type `STUDY_EDITED` must be pushed when the upgrade is done.
    event_bus = Mock()

    # The `upgrade_study()` function raise an exception
    upgrade_study_mock.side_effect = Exception("INVALID_UPGRADE")

    # Prepare the task for an upgrade
    task = StudyUpgraderTask(
        study_id,
        target_version,
        repository=repository,
        storage_service=storage_service,
        cache_service=cache_service,
        event_bus=event_bus,
    )

    # The task is called with a `TaskUpdateNotifier` a parameter.
    # Some messages could be emitted using the notifier (not a requirement).
    notifier = Mock()
    with pytest.raises(Exception, match="INVALID_UPGRADE"):
        task(notifier)

    # The study must not be updated in the database
    actual_study: RawStudy = db.session.query(Study).get(study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == old_version

    # No event must be emitted
    event_bus.push.assert_not_called()
