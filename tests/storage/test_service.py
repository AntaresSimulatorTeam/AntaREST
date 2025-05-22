# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import contextlib
import os
import textwrap
import typing as t
import uuid
from configparser import MissingSectionHeaderError
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from unittest.mock import ANY, Mock, call, patch, seal

import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session  # type: ignore
from starlette.responses import Response

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import StudyVariantUpgradeError, TaskAlreadyRunning
from antarest.core.filetransfer.model import FileDownload, FileDownloadTaskDTO
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.model import JSON, SUB_JSON, PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.core.tasks.model import TaskDTO, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, GroupDTO, Role, User
from antarest.login.service import LoginService
from antarest.login.utils import current_user_context
from antarest.matrixstore.service import MatrixService
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_VERSION_7_2,
    ExportFormat,
    MatrixAggregationResultDTO,
    MatrixIndex,
    OwnerInfo,
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
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository
from antarest.study.service import MAX_MISSING_STUDY_TIMEOUT, StudyService, StudyUpgraderTask
from antarest.study.storage.output_service import OutputService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    DistrictSet,
    FileStudyTreeConfig,
    LinkConfig,
    Mode,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_dispatchers import OutputStorageDispatcher
from antarest.study.storage.utils import (
    assert_permission,
    assert_permission_on_studies,
    is_output_archived,
    study_matcher,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from antarest.worker.archive_worker import ArchiveTaskArgs
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import with_admin_user, with_db_context

JWT_USER = JWTUser(id=0, impersonator=0, type="users")


def with_jwt_user(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
    @wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        with current_user_context(JWT_USER):
            return f(*args, **kwargs)

    return wrapper


def build_study_service(
    raw_study_service: RawStudyService,
    repository: StudyMetadataRepository,
    config: Config,
    user_service: LoginService = Mock(spec=LoginService),
    cache_service: ICache = Mock(spec=ICache),
    variant_study_service: VariantStudyService = Mock(spec=VariantStudyService),
    task_service: ITaskService = Mock(spec=ITaskService),
    event_bus: IEventBus = Mock(spec=IEventBus),
) -> StudyService:
    return StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        command_context=Mock(),
        user_service=user_service,
        repository=repository,
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=Mock(),
        cache_service=cache_service,
        config=config,
    )


def study_to_dto(study: Study) -> StudyMetadataDTO:
    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=study.version,
        created=str(study.created_at),
        updated=str(study.updated_at),
        workspace=DEFAULT_WORKSPACE_NAME,
        managed=True,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=(
            OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name="Unknown")
        ),
        groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=study.additional_data.horizon,
        scenario=None,
        status=None,
        doc=None,
        folder=None,
    )


@pytest.mark.unit_test
def test_study_listing(db_session: Session) -> None:
    bob = User(id=2, name="bob")
    alice = User(id=3, name="alice")

    study_version = "810"
    a = RawStudy(
        id="A",
        owner=bob,
        type="rawstudy",
        name="A",
        version=study_version,
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
        version=study_version,
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
        version=study_version,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        path="",
        workspace="other2",
        additional_data=StudyAdditionalData(),
    )

    # Add some studies in the database
    db_session.add_all([a, b, c])
    db_session.commit()

    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.get_study_information.side_effect = study_to_dto

    cache = Mock(spec=ICache)
    cache.get.return_value = None

    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    repository = StudyMetadataRepository(cache_service=Mock(spec=ICache), session=db_session)
    service = build_study_service(raw_study_service, repository, config, cache_service=cache)
    user = JWTUser(id=2, impersonator=2, type="users")

    # retrieve studies that are not managed
    # use the db recorder to check that:
    # 1- retrieving studies information requires only 1 query
    # 2- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        studies = service.get_studies_information(
            study_filter=StudyFilter(managed=False, access_permissions=AccessPermissions.for_user(user)),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    # verify that we get the expected studies information
    expected_result = {e.id: e for e in map(lambda x: study_to_dto(x), [c])}
    assert expected_result == studies

    # retrieve managed studies
    # use the db recorder to check that:
    # 1- retrieving studies information requires only 1 query
    # 2- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        studies = service.get_studies_information(
            study_filter=StudyFilter(managed=True, access_permissions=AccessPermissions.for_user(user)),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    # verify that we get the expected studies information
    expected_result = {e.id: e for e in map(lambda x: study_to_dto(x), [a])}
    assert expected_result == studies

    # retrieve studies regardless of whether they are managed or not
    # use the db recorder to check that:
    # 1- retrieving studies information requires only 1 query
    # 2- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        studies = service.get_studies_information(
            study_filter=StudyFilter(managed=None, access_permissions=AccessPermissions.for_user(user)),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    # verify that we get the expected studies information
    expected_result = {e.id: e for e in map(lambda x: study_to_dto(x), [a, c])}
    assert expected_result == studies

    # in previous versions cache was used, verify that it is not used anymore
    # check that:
    # 1- retrieving studies information still requires 1 query
    # 2- the `put` method of `cache` was never used
    with DBStatementRecorder(db_session.bind) as db_recorder:
        studies = service.get_studies_information(
            study_filter=StudyFilter(managed=None, access_permissions=AccessPermissions.for_user(user)),
        )
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)
    with contextlib.suppress(AssertionError):
        cache.put.assert_any_call()

    # verify that we get the expected studies information
    assert expected_result == studies


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_sync_studies_from_disk() -> None:
    now = datetime.utcnow()

    # Studies in DB
    ma = RawStudy(id="a", path="a", workspace="workspace1")
    mb = RawStudy(id="b", path="b")
    mc = RawStudy(
        id="c",
        path="c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace="workspace1",
        owner=User(id=0),
    )
    md = RawStudy(
        id="d",
        path="d",
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT + 1),
        workspace="workspace1",
    )
    me = RawStudy(
        id="e",
        path="e",
        folder="e",
        name="e",
        created_at=now,
        missing=datetime.utcnow() - timedelta(MAX_MISSING_STUDY_TIMEOUT - 1),
        workspace="workspace1",
    )
    mg = RawStudy(
        id="g",
        path="g",
        folder="g",
        name="g",
        created_at=now,
        missing=None,
        workspace=DEFAULT_WORKSPACE_NAME,
    )

    # Folders scanned
    fa = StudyFolder(path=Path("a"), workspace="workspace1", groups=[])
    fa2 = StudyFolder(path=Path("a"), workspace="workspace2", groups=[])
    fc = StudyFolder(path=Path("c"), workspace="workspace1", groups=[])
    fe = StudyFolder(path=Path("e"), workspace="workspace1", groups=[])
    ff = StudyFolder(path=Path("f"), workspace="workspace1", groups=[])
    ff2 = StudyFolder(path=Path("f"), workspace="workspace2", groups=[])

    # setup existing studies
    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, md, me, mg]]
    config = Config(
        storage=StorageConfig(
            workspaces={
                "workspace1": WorkspaceConfig(),
                "workspace2": WorkspaceConfig(),
            }
        )
    )
    service = build_study_service(Mock(), repository, config)

    # call function with scanned folders
    service.sync_studies_on_disk([fa, fa2, fc, fe, ff, ff2])

    # here d exists in DB but not on disc so it should be removed
    # notice b also exists in DB but not on disk but it's not deleted yet,  rather it's marked for deletion by a save call
    repository.delete.assert_called_once_with(md.id)
    # (f, workspace1) exist on disc but not in DB so it should be added
    # The studies a and f exists in workspace 2, studies under the same path exists in workspace 1,
    # we check that we indeed save them in DB
    repository.save.assert_has_calls(
        [
            call(RawStudy(id="b", path="b", missing=ANY)),
            call(
                RawStudy(
                    id=ANY,
                    path="a",
                    name="a",
                    folder="a",
                    workspace="workspace2",
                    missing=None,
                    public_mode=PublicMode.FULL,
                )
            ),
            call(
                RawStudy(id="e", path="e", name="e", folder="e", workspace="workspace1", missing=None, created_at=now)
            ),
            call(
                RawStudy(
                    id=ANY,
                    path="f",
                    name="f",
                    folder="f",
                    workspace="workspace1",
                    missing=None,
                    public_mode=PublicMode.FULL,
                )
            ),
            call(
                RawStudy(
                    id=ANY,
                    path="f",
                    name="f",
                    folder="f",
                    workspace="workspace2",
                    missing=None,
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
        workspace="workspace1",
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
    fc = StudyFolder(path=Path("directory/c"), workspace="workspace1", groups=[])
    fe = StudyFolder(path=Path("directory/e"), workspace="workspace1", groups=[])
    ff = StudyFolder(path=Path("directory/f"), workspace="workspace1", groups=[])

    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, md, me]]
    config = Config(storage=StorageConfig(workspaces={"workspace1": WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config)

    service.sync_studies_on_disk([fc, fe, ff], directory=Path("directory"))

    repository.delete.assert_called_once_with(md.id)
    repository.save.assert_called_with(
        RawStudy(
            id=ANY,
            path=f"directory{os.sep}f",
            name="f",
            folder="directory/f",
            created_at=ANY,
            missing=None,
            public_mode=PublicMode.FULL,
            workspace="workspace1",
        )
    )


@with_db_context
def test_remove_duplicate(db_session: Session) -> None:
    with db_session:
        db_session.add(RawStudy(id="a", path="/path/to/a"))
        db_session.add(RawStudy(id="b", path="/path/to/a"))
        db_session.add(RawStudy(id="c", path="/path/to/c"))
        db_session.commit()
        study_count = db_session.query(RawStudy).filter(RawStudy.path == "/path/to/a").count()
        assert study_count == 2  # there are 2 studies with same path before removing duplicates

    with db_session:
        repository = StudyMetadataRepository(Mock(), db_session)
        config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
        service = build_study_service(Mock(), repository, config)
        service.remove_duplicates()

    # example with 1 duplicate with same path
    with db_session:
        study_count = db_session.query(RawStudy).filter(RawStudy.path == "/path/to/a").count()
    assert study_count == 1
    # example with no duplicates with same path
    with db_session:
        study_count = db_session.query(RawStudy).filter(RawStudy.path == "/path/to/c").count()
    assert study_count == 1


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_create_study() -> None:
    # Mock
    repository = Mock()

    # Input
    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    expected = RawStudy(
        id=str(uuid.uuid4()),
        name="new-study",
        version="700",
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

    jwt_user = JWT_USER
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt_user):
            service.create_study("new-study", STUDY_VERSION_7_2, ["my-group"])

    jwt_user.groups = [JWTGroup(id="my-group", name="group", role=RoleType.WRITER)]
    with current_user_context(jwt_user):
        service.create_study("new-study", STUDY_VERSION_7_2, ["my-group"])

    study_service.create.assert_called()
    repository.save.assert_called_once_with(expected)


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_save_metadata() -> None:
    # Mock
    repository = Mock()

    study_id = str(uuid.uuid4())

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
    jwt = JWT_USER
    jwt.groups = [JWTGroup(id="my-group", name="group", role=RoleType.ADMIN)]
    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    # Expected
    study = RawStudy(
        id=study_id,
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config)

    service.user_service.get_user.return_value = user  # type: ignore
    with current_user_context(jwt):
        service._save_study(RawStudy(id=study_id, workspace=DEFAULT_WORKSPACE_NAME))
    repository.save.assert_called_once_with(study)


@with_jwt_user
@pytest.mark.unit_test
def test_download_output() -> None:
    study_service = Mock()
    repository = Mock(spec=StudyMetadataRepository)

    study_version = 870
    input_study = RawStudy(
        id="c",
        path="c",
        name="c",
        version=str(study_version),
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
        links={"west": LinkConfig(filters_synthesis=[], filters_year=[])},
        thermals=[],
        renewables=[],
        filters_synthesis=[],
        filters_year=[],
    )

    sim = Simulation(
        name="",
        date="",
        mode=Mode.ECONOMY,
        nbyears=1,
        synthesis=True,
        by_year=True,
        error=False,
        playlist=[0],
        xpansion="",
    )
    file_study_tree_config = FileStudyTreeConfig(
        study_path=Path(input_study.path),
        path=Path(input_study.path),
        study_id=str(uuid.uuid4()),
        version=StudyVersion.parse(input_study.version),
        areas={"east": area},
        sets={"north": DistrictSet()},
        outputs={"output-id": sim},
        store_new_set=False,
    )
    file_study_tree = Mock(spec=FileStudyTree, config=file_study_tree_config)

    repository.get.return_value = input_study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, repository, config)
    storage = OutputStorageDispatcher(
        service.storage_service.raw_study_service, service.storage_service.variant_study_service
    )
    output_service = OutputService(
        service,
        storage,
        service.task_service,
        service.file_transfer_manager,
        service.event_bus,
    )

    res_study = {"columns": [["H. VAL", "Euro/MWh"]], "data": [[0.5]]}
    res_study_details = {
        "columns": [["some cluster", "Euro/MWh"]],
        "data": [[0.8]],
    }
    study_service.get_raw.return_value = FileStudy(config=file_study_tree_config, tree=file_study_tree)
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
    file_study_tree.get.side_effect = [
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
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5]),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=[0.8]),
                    ]
                },
            )
        ],
        warnings=[],
    )
    res = t.cast(
        Response,
        output_service.download_outputs(
            "study-id", "output-id", input_data, use_task=False, filetype=ExportFormat.JSON
        ),
    )
    assert MatrixAggregationResultDTO.model_validate_json(res.body) == res_matrix

    # AREA TYPE - ZIP & TASK
    export_file_download = FileDownload(
        id="download-id",
        filename="filename",
        name="name",
        ready=False,
        path="path",
        expiration_date=datetime.utcnow(),
    )
    service.file_transfer_manager.request_download.return_value = export_file_download  # type: ignore
    task_id = "task-id"
    service.task_service.add_task.return_value = task_id  # type: ignore

    result = t.cast(
        FileDownloadTaskDTO,
        output_service.download_outputs("study-id", "output-id", input_data, use_task=True, filetype=ExportFormat.ZIP),
    )

    res_file_download = FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)
    assert result == res_file_download

    # LINK TYPE
    input_data.type = StudyDownloadType.LINK
    input_data.filter = ["east>west"]
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east^west",
                type=StudyDownloadType.LINK,
                data={"1": [TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5])]},
            )
        ],
        warnings=[],
    )
    res = t.cast(
        Response,
        output_service.download_outputs(
            "study-id", "output-id", input_data, use_task=False, filetype=ExportFormat.JSON
        ),
    )
    assert MatrixAggregationResultDTO.model_validate_json(res.body) == res_matrix

    # CLUSTER TYPE
    input_data.type = StudyDownloadType.DISTRICT
    input_data.filter = []
    input_data.filterIn = "n"
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="north",
                type=StudyDownloadType.DISTRICT,
                data={
                    "1": [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=[0.5]),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=[0.8]),
                    ]
                },
            )
        ],
        warnings=[],
    )
    res = t.cast(
        Response,
        output_service.download_outputs(
            "study-id", "output-id", input_data, use_task=False, filetype=ExportFormat.JSON
        ),
    )
    assert MatrixAggregationResultDTO.model_validate_json(res.body) == res_matrix


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_change_owner() -> None:
    study_id = str(uuid.uuid4())
    alice = User(id=2)
    bob = User(id=3, name="Bob")
    jwt_user = JWTUser(id=2, impersonator=2, type="users")

    file_study = Mock(spec=FileStudy, get_node=Mock(return_value=Mock(spec=IniFileNode)))

    repository = Mock(spec=StudyMetadataRepository)
    user_service = Mock()
    study_service = Mock(spec=RawStudyService)
    study_service.get_raw.return_value = file_study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    variant_study_service = Mock(
        spec=VariantStudyService,
        command_factory=Mock(
            spec=GeneratorMatrixConstants,
            command_context=Mock(spec=CommandContext),
        ),
    )
    service = build_study_service(
        study_service,
        repository,
        config,
        user_service=user_service,
        variant_study_service=variant_study_service,
    )

    study = RawStudy(id=study_id, owner=alice)
    repository.get.return_value = study
    user_service.get_user.return_value = bob
    service._edit_study_using_command = Mock()

    with current_user_context(jwt_user):
        service.change_owner(study_id, 2)

    service._edit_study_using_command.assert_called_once_with(study=study, url="study/antares/author", data="Bob")
    user_service.get_user.assert_called_once_with(2)
    repository.save.assert_called_with(RawStudy(id=study_id, owner=bob, last_access=ANY))
    repository.save.assert_called_with(RawStudy(id=study_id, owner=bob))

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt_user):
            service.change_owner(study_id, 1)


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_manage_group() -> None:
    study_id = str(uuid.uuid4())
    alice = User(id=1)
    group_a = Group(id="a", name="Group A")
    group_b = Group(id="b", name="Group B")
    user = JWTUser(id=2, impersonator=2, type="users")
    group_a_admin = JWTGroup(id="a", name="Group A", role=RoleType.ADMIN)

    repository = Mock()
    user_service = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config, user_service=user_service)

    repository.get.return_value = Study(id=study_id, owner=alice, groups=[group_a])

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(user):
            service.add_group(study_id, "b")

    user.groups.append(group_a_admin)
    user_service.get_group.return_value = group_b
    with current_user_context(user):
        service.add_group(study_id, "b")

    user_service.get_group.assert_called_once_with("b")
    repository.save.assert_called_with(Study(id=study_id, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = Study(id=study_id, owner=alice, groups=[group_a, group_b])
    with current_user_context(user):
        service.add_group(study_id, "b")
        user_service.get_group.assert_called_with("b")
    repository.save.assert_called_with(Study(id=study_id, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = Study(id=study_id, owner=alice, groups=[group_a, group_b])
    with current_user_context(user):
        service.remove_group(study_id, "a")
    repository.save.assert_called_with(Study(id=study_id, owner=alice, groups=[group_b]))


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_set_public_mode() -> None:
    study_id = str(uuid.uuid4())
    group_admin = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
    user = JWTUser(id=2, impersonator=2, type="users")

    repository = Mock()
    user_service = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(Mock(), repository, config, user_service=user_service)

    repository.get.return_value = Study(id=study_id)

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(user):
            service.set_public_mode(study_id, PublicMode.FULL)

    user.groups.append(group_admin)
    with current_user_context(user):
        service.set_public_mode(study_id, PublicMode.FULL)
    repository.save.assert_called_with(Study(id=study_id, public_mode=PublicMode.FULL))


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_check_errors() -> None:
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
        StudyMetadataDTO.model_construct(id="1", folder="abc/de", workspace="hello")
    )
    assert study_matcher(name=None, folder="ab", workspace="hello")(
        StudyMetadataDTO.model_construct(id="1", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name=None, folder="abd", workspace="hello")(
        StudyMetadataDTO.model_construct(id="1", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name=None, folder="ab", workspace="hello")(
        StudyMetadataDTO.model_construct(id="1", workspace="hello")
    )
    assert study_matcher(name="f", folder=None, workspace="hello")(
        StudyMetadataDTO.model_construct(id="1", name="foo", folder="abc/de", workspace="hello")
    )
    assert not study_matcher(name="foob", folder=None, workspace="hell")(
        StudyMetadataDTO.model_construct(id="1", name="foo", folder="abc/de", workspace="hello")
    )


# noinspection PyArgumentList
@pytest.mark.unit_test
def test_assert_permission() -> None:
    study_id = str(uuid.uuid4())
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
    repository.get.return_value = Study(id=study_id, owner=wrong)
    study = service.get_study(study_id)
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.READ)

    # good owner
    study = Study(id=study_id, owner=good)
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # wrong group
    study = Study(id=study_id, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.READ)

    # good group
    study = Study(id=study_id, owner=wrong, groups=[Group(id="my-group")])
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # super admin can do whatever he wants..
    study = Study(id=study_id)
    with current_user_context(admin):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # when study found in workspace without group
    study = Study(id=study_id, public_mode=PublicMode.FULL)
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.READ)
        assert_permission(study, StudyPermissionType.WRITE)
        assert_permission(study, StudyPermissionType.RUN)

    # some group roles
    study = Study(id=study_id, owner=wrong, groups=[Group(id="my-group-2")])
    with current_user_context(jwt_2):
        with pytest.raises(UserHasNotPermissionError):
            assert_permission(study, StudyPermissionType.WRITE)
        assert_permission(study, StudyPermissionType.READ)


class UserGroups(t.TypedDict):
    name: str
    role: RoleType
    users: t.Sequence[str]


def test_assert_permission_on_studies(db_session: Session) -> None:
    # Given the following user groups :
    user_groups: t.Sequence[UserGroups] = [
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
        Study(id=uuid.uuid4(), name="Main Study", owner_id=jwt_users["John"].id, groups=[writers]),
        Study(id=uuid.uuid4(), name="Variant Study 1", owner_id=jwt_users["Jane"].id, groups=[writers]),
        Study(id=uuid.uuid4(), name="Variant Study 2", owner_id=jwt_users["Jane"].id, groups=[writers]),
    ]

    # All admin and writers should have WRITE access to the studies.
    # Other members of the group should have no access.
    for user_name, jwt_user in jwt_users.items():
        has_access = any(jwt_group.name in {"admin", "Writers"} for jwt_group in jwt_user.groups)
        with current_user_context(jwt_user):
            if has_access:
                assert_permission_on_studies(studies, StudyPermissionType.WRITE)
            else:
                with pytest.raises(UserHasNotPermissionError):
                    assert_permission_on_studies(studies, StudyPermissionType.WRITE)

    # Jack creates a additional variant study and adds it to the readers and writers groups.
    readers = db_session.query(Group).filter(Group.name == "Readers").one()
    studies.append(
        Study(id=uuid.uuid4(), name="Variant Study 3", owner_id=jwt_users["Jack"].id, groups=[readers, writers])
    )

    # All admin and writers should have READ access to the studies.
    # Other members of the group should have no access, because they don't have access to the writers-only studies.
    for user_name, jwt_user in jwt_users.items():
        has_access = any(jwt_group.name in {"admin", "Writers"} for jwt_group in jwt_user.groups)
        with current_user_context(jwt_user):
            if has_access:
                assert_permission_on_studies(studies, StudyPermissionType.READ)
            else:
                with pytest.raises(UserHasNotPermissionError):
                    assert_permission_on_studies(studies, StudyPermissionType.WRITE)

    # Everybody should have access to the last study, because it is in the readers and writers group.
    for user_name, jwt_user in jwt_users.items():
        with current_user_context(jwt_user):
            assert_permission_on_studies(studies[-1:], StudyPermissionType.READ)


@with_admin_user
@pytest.mark.unit_test
def test_delete_study_calls_callback(tmp_path: Path) -> None:
    study_uuid = str(uuid.uuid4())
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
    service.storage_service.variant_study_service.has_children.return_value = False  # type: ignore

    service.delete_study(study_uuid, children=False)

    callback.assert_called_once_with(study_uuid)


@with_admin_user
@pytest.mark.unit_test
def test_delete_with_prefetch(tmp_path: Path) -> None:
    study_uuid = str(uuid.uuid4())

    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(Config(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(),
        Mock(),
        raw_study_service,
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
    variant_study_repository.has_children.return_value = False

    # if this fails, it may mean the study metadata mock is missing some attribute definition
    # this test is here to prevent errors if we add attribute fetching from child classes
    # (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
        children=False,
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
    study_mock.generation_task = None
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    study_metadata_repository.get.return_value = study_mock
    variant_study_repository.has_children.return_value = False

    # if this fails, it may means the study metadata mock is missing some definition
    # this test is here to prevent errors if we add attribute fetching from child classes (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
        children=False,
    )


@with_admin_user
def test_delete_recursively(tmp_path: Path) -> None:
    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(Config(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(),
        Mock(),
        raw_study_service,
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
        _study_dir = tmp_path / str(uuid.uuid4())
        _study_dir.mkdir()
        if variant:
            _study_data = _study_dir / "snapshot"
            _study_data.mkdir()
        else:
            _study_data = _study_dir
        (_study_data / "study.antares").touch()
        return str(_study_dir)

    study_path = create_study_fs_mock()
    study_mock = RawStudy(
        archived=False,
        id="my_study",
        path=study_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
        last_access=datetime.utcnow(),
    )

    v1 = VariantStudy(id="variant_1", path=create_study_fs_mock(variant=True))
    v2 = VariantStudy(id="variant_2", path=create_study_fs_mock(variant=True))
    v3 = VariantStudy(id="sub_variant_1", path=create_study_fs_mock(variant=True))

    def get_study(study_id: str) -> Study:
        if study_id == "my_study":
            return study_mock
        elif study_id == "variant_1":
            return v1
        elif study_id == "variant_2":
            return v2
        elif study_id == "sub_variant_1":
            return v3
        raise ValueError(f"Unexpected study id: {study_id}")

    class ChildrenProvider:
        def __init__(self):
            self.c0 = 0
            self.c1 = 0

        def get_children(self, parent_id: str) -> t.List[Study]:
            if parent_id == "my_study":
                if self.c0 > 0:
                    return []
                self.c0 = 1
                return [v1, v2]
            elif parent_id == "variant_1":
                if self.c1 > 0:
                    return []
                self.c1 = 1
                return [v3]
            elif parent_id == "variant_2":
                return []
            elif parent_id == "sub_variant_1":
                return []
            raise ValueError(f"Unexpected study id: {parent_id}")

    class HasChildrenProvider:
        def __init__(self):
            self.c1 = 0
            self.c2 = 0

        def has_children(self, study_id: str) -> bool:
            if study_id == "my_study":
                if self.c1 > 0:
                    return False
                self.c1 = 1
                return True
            elif study_id == "variant_1":
                if self.c2 > 0:
                    return False
                self.c2 = 1
                return True
            elif study_id == "variant_2":
                return False
            elif study_id == "sub_variant_1":
                return False
            raise ValueError(f"Unexpected study id: {study_id}")

    children_provider = ChildrenProvider()
    hash_children_provider = HasChildrenProvider()
    study_metadata_repository.get = get_study
    variant_study_repository.get = get_study
    variant_study_repository.get_children = children_provider.get_children
    variant_study_repository.has_children = hash_children_provider.has_children

    service.delete_study(
        "my_study",
        children=True,
    )


@pytest.mark.unit_test
def test_edit_study_with_command() -> None:
    study_id = str(uuid.uuid4())

    service = build_study_service(
        raw_study_service=Mock(),
        repository=Mock(),
        config=Mock(),
    )
    command = Mock()
    service._create_edit_study_command = Mock(return_value=command)
    study_service = Mock(spec=RawStudyService)
    service.storage_service.get_storage = Mock(return_value=study_service)
    raw_study = Mock(spec=RawStudy)
    raw_study.version = "880"
    raw_study.id = study_id

    service._edit_study_using_command(study=raw_study, url="", data=[])
    command.apply.assert_called()

    variant_study = Mock(spec=VariantStudy)
    variant_study.version = "880"
    study_service = Mock(spec=VariantStudyService)
    service.storage_service.get_storage = Mock(return_value=study_service)
    service._edit_study_using_command(study=variant_study, url="", data=[])
    service.storage_service.variant_study_service.append_commands.assert_called_once()


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
    tree_node: INode[JSON, t.Union[str, int, bool, float, bytes, JSON], JSON],
    url: str,
    data: SUB_JSON,
    expected_name: str,
) -> None:
    matrix_id = "matrix_id"

    command_context = CommandContext(
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        matrix_service=Mock(spec=MatrixService, create=Mock(return_value=matrix_id)),
    )

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        repository=Mock(spec=StudyMetadataRepository),
        config=Mock(spec=Config),
        variant_study_service=Mock(
            spec=VariantStudyService,
            command_factory=Mock(spec=GeneratorMatrixConstants, command_context=command_context),
        ),
    )

    command = service._create_edit_study_command(
        tree_node=tree_node, url=url, data=data, study_version=StudyVersion.parse("880")
    )

    assert command.command_name.value == expected_name


@with_admin_user
def test_unarchive_output(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    study_name = "My Study"
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
        to_json_summary=Mock(return_value={"id": study_id, "name": study_name}),
    )
    # The `name` attribute cannot be mocked during creation of the mock object
    # https://stackoverflow.com/a/62552149/1513933
    study_mock.name = study_name

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        repository=Mock(spec=StudyMetadataRepository, get=Mock(return_value=study_mock)),
        config=Mock(spec=Config),
    )

    service.task_service.reset_mock()

    output_id = "some-output"
    service.task_service.add_worker_task.return_value = None  # type: ignore
    service.task_service.list_tasks.return_value = []  # type: ignore
    (tmp_path / "output" / f"{output_id}.zip").mkdir(parents=True, exist_ok=True)
    storage = OutputStorageDispatcher(
        service.storage_service.raw_study_service, service.storage_service.variant_study_service
    )
    output_service = OutputService(
        service,
        storage,
        service.task_service,
        Mock(),
        Mock(),
    )
    output_service.unarchive_output(
        study_id,
        output_id,
        keep_src_zip=True,
    )

    service.task_service.add_worker_task.assert_called_once_with(
        TaskType.UNARCHIVE,
        "unarchive_other_workspace",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_id}.zip"),
            dest=str(tmp_path / "output" / output_id),
            remove_src=False,
        ).model_dump(),
        name=f"Unarchive output {study_name}/{output_id} ({study_id})",
        ref_id=study_id,
    )
    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Unarchive output {study_name}/{output_id} ({study_id})",
        task_type=TaskType.UNARCHIVE,
        ref_id=study_id,
        progress=None,
        custom_event_messages=None,
    )


@with_admin_user
def test_archive_output_locks(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    study_name = "My Study"
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
        to_json_summary=Mock(return_value={"id": study_id, "name": study_name}),
    )
    # The `name` attribute cannot be mocked during creation of the mock object
    # https://stackoverflow.com/a/62552149/1513933
    study_mock.name = study_name

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        repository=Mock(spec=StudyMetadataRepository, get=Mock(return_value=study_mock)),
        config=Mock(spec=Config),
    )

    service.task_service.reset_mock()

    output_zipped = "some-output_zipped"
    output_unzipped = "some-output_unzipped"
    service.task_service.add_worker_task.return_value = None  # type: ignore
    (tmp_path / "output" / output_unzipped).mkdir(parents=True)
    (tmp_path / "output" / f"{output_zipped}.zip").touch()
    service.task_service.list_tasks.side_effect = [
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_zipped}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_zipped} ({study_id})",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_unzipped}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_unzipped} ({study_id})",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(datetime.utcnow()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [],
    ]
    storage = OutputStorageDispatcher(
        service.storage_service.raw_study_service, service.storage_service.variant_study_service
    )
    output_service = OutputService(
        service,
        storage,
        service.task_service,
        Mock(),
        Mock(),
    )
    with pytest.raises(TaskAlreadyRunning):
        output_service.unarchive_output(
            study_id,
            output_zipped,
            keep_src_zip=True,
        )

    with pytest.raises(TaskAlreadyRunning):
        output_service.unarchive_output(
            study_id,
            output_zipped,
            keep_src_zip=True,
        )

    with pytest.raises(TaskAlreadyRunning):
        output_service.archive_output(
            study_id,
            output_unzipped,
        )

    with pytest.raises(TaskAlreadyRunning):
        output_service.archive_output(
            study_id,
            output_unzipped,
        )

    output_service.unarchive_output(
        study_id,
        output_zipped,
        keep_src_zip=True,
    )

    service.task_service.add_worker_task.assert_called_once_with(
        TaskType.UNARCHIVE,
        "unarchive_other_workspace",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_zipped}.zip"),
            dest=str(tmp_path / "output" / output_zipped),
            remove_src=False,
        ).model_dump(),
        name=f"Unarchive output {study_name}/{output_zipped} ({study_id})",
        ref_id=study_id,
    )
    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Unarchive output {study_name}/{output_zipped} ({study_id})",
        task_type=TaskType.UNARCHIVE,
        ref_id=study_id,
        progress=None,
        custom_event_messages=None,
    )


@with_admin_user
def test_get_save_logs(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    study_name = "My Study"
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
        to_json_summary=Mock(return_value={"id": study_id, "name": study_name}),
    )
    # The `name` attribute cannot be mocked during creation of the mock object
    # https://stackoverflow.com/a/62552149/1513933
    study_mock.name = study_name

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        repository=Mock(spec=StudyMetadataRepository, get=Mock(return_value=study_mock)),
        config=Mock(spec=Config),
    )

    output_config = Mock(get_file=Mock(return_value="output_id"), archived=False)

    file_study_config = FileStudyTreeConfig(tmp_path, tmp_path, "study_id", 0, archive_path=None)
    file_study_config.outputs = {"output_id": output_config}

    context = Mock()
    context.resolver.get_matrix.return_value = None
    service.storage_service.raw_study_service.get_raw.return_value = FileStudy(  # type: ignore
        config=file_study_config,
        tree=FileStudyTree(context, file_study_config),
    )

    output_path = tmp_path / "output"
    output_path.mkdir()
    (output_path / "output_id").mkdir()
    (output_path / "logs").mkdir()

    possible_log_paths = [
        output_path / "output_id" / "antares-out.log",
        output_path / "output_id" / "simulation.log",
        output_path / "logs" / "job_id-out.log",
        output_path / "logs" / "output_id-out.log",
    ]

    for log_path in possible_log_paths:
        log_path.write_text("some log 2")
        assert (
            service.get_logs(
                study_id,
                "output_id",
                "job_id",
                False,
            )
            == "some log 2"
        )
        log_path.unlink()

    service.save_logs(study_id, "job_id", "out.log", "some log")
    assert (
        service.get_logs(
            study_id,
            "output_id",
            "job_id",
            False,
        )
        == "some log"
    )

    service.save_logs(study_id, "job_id", "err.log", "some log 3")
    assert (
        service.get_logs(
            study_id,
            "output_id",
            "job_id",
            True,
        )
        == "some log 3"
    )


@with_admin_user
def test_task_upgrade_study(tmp_path: Path) -> None:
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
    service.repository.has_children.return_value = False  # type: ignore
    service.repository.get.return_value = study_mock  # type: ignore

    study_id = "my_study"
    service.task_service.reset_mock()  # type: ignore
    service.task_service.list_tasks.side_effect = [
        [
            TaskDTO(
                id="1",
                name=f"Upgrade study my_study ({study_id}) to version 800",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(datetime.utcnow()),  # type: ignore
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
        )

    service.upgrade_study(
        study_id,
        target_version="",
    )

    service.task_service.add_task.assert_called_once_with(
        ANY,
        f"Upgrade study my_study ({study_id}) to version 800",
        task_type=TaskType.UPGRADE_STUDY,
        ref_id=study_id,
        progress=None,
        custom_event_messages=None,
    )

    # check that a variant study or a raw study with children cannot be upgraded
    parent_raw_study = Mock(
        spec=RawStudy,
        archived=False,
        id="parent_raw_study",
        name="parent_raw_study",
        path=tmp_path,
        version="720",
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )
    study_mock.name = "parent_raw_study"
    study_mock.to_json_summary.return_value = {"id": "parent_raw_study", "name": "parent_raw_study"}
    service.repository.has_children.return_value = True  # type: ignore
    service.repository.get.return_value = parent_raw_study  # type: ignore

    with pytest.raises(StudyVariantUpgradeError):
        service.upgrade_study(
            "parent_raw_study",
            target_version="",
        )

    variant_study = Mock(
        spec=VariantStudy,
        archived=False,
        id="variant_study",
        name="variant_study",
        path=tmp_path,
        version="720",
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
    )

    study_mock.name = "variant_study"
    study_mock.to_json_summary.return_value = {"id": "variant_study", "name": "variant_study"}
    service.repository.has_children.return_value = True  # type: ignore
    service.repository.get.return_value = variant_study  # type: ignore

    with pytest.raises(StudyVariantUpgradeError):
        service.upgrade_study(
            "variant_study",
            target_version="",
        )


@with_db_context
@patch("antarest.study.storage.study_upgrader.StudyUpgrader.upgrade")
@pytest.mark.parametrize("workspace", ["other_workspace", DEFAULT_WORKSPACE_NAME])
def test_upgrade_study__raw_study__nominal(
    upgrade_study_mock: Mock,
    tmp_path: Path,
    workspace: str,
) -> None:
    study_id = str(uuid.uuid4())
    study_name = "my_study"
    target_version = "800"
    current_version = "720"
    (tmp_path / "study.antares").touch()
    (tmp_path / "study.antares").write_text(
        textwrap.dedent(
            f"""
                [antares]
                version = {current_version}
                caption =
                created = 1682506382.235618
                lastsave = 1682506382.23562
                author = Unknown"""
        )
    )

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

    upgrade_study_mock.assert_called_once_with()

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
@patch("antarest.study.storage.study_upgrader.StudyUpgrader.upgrade")
def test_upgrade_study__variant_study__nominal(
    upgrade_study_mock: Mock,
    tmp_path: Path,
) -> None:
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
def test_upgrade_study__raw_study__failed(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    study_name = "my_study"
    target_version = "800"
    old_version = "720"
    (tmp_path / "study.antares").touch()
    (tmp_path / "study.antares").write_text(f"version = {old_version}")
    # The study.antares file doesn't have an header the upgrade should fail.

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
    with pytest.raises(MissingSectionHeaderError, match="File contains no section headers"):
        task(notifier)

    # The study must not be updated in the database
    actual_study: RawStudy = db.session.query(Study).get(study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == old_version

    # No event must be emitted
    event_bus.push.assert_not_called()


@pytest.mark.unit_test
def test_is_output_archived(tmp_path) -> None:
    assert not is_output_archived(path_output=Path("fake_path"))
    assert is_output_archived(path_output=Path("fake_path.zip"))

    zipped_output_path = tmp_path / "output.zip"
    zipped_output_path.mkdir(parents=True)
    assert is_output_archived(path_output=zipped_output_path)
    assert is_output_archived(path_output=tmp_path / "output")

    zipped_with_suffix = tmp_path / "output_1.4.3.zip"
    zipped_with_suffix.mkdir(parents=True)
    assert is_output_archived(path_output=zipped_with_suffix)
    assert is_output_archived(path_output=tmp_path / "output_1.4.3")
