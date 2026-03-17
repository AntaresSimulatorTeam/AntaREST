# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import logging
import os
import textwrap
import typing as t
import uuid
from configparser import MissingSectionHeaderError
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from unittest.mock import ANY, Mock, patch, seal

import pytest
from _pytest.logging import LogCaptureFixture
from antares.study.version import StudyVersion
from fastapi import HTTPException
from sqlalchemy.orm import Session

from antarest.blobstore.service import BlobService
from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import (
    StudyDeletionNotAllowed,
    StudyNotFoundError,
    StudyVariantUpgradeError,
    TaskAlreadyRunning,
    UnsupportedOperationOnThisStudyType,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.model import JSON, SUB_JSON, PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.roles import RoleType
from antarest.core.tasks.model import TaskDTO, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.login.model import Group, GroupDTO, Role, User
from antarest.login.service import LoginService
from antarest.login.utils import current_user_context
from antarest.matrixstore.service import MatrixService
from antarest.output.storage.output_storage import OutputMetadata
from antarest.study.directory_service import DirectoryService
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    STUDY_VERSION_7_2,
    OwnerInfo,
    RawStudy,
    StorageMode,
    Study,
    StudyContentStatus,
    StudyFolder,
    StudyMetadataDTO,
    StudyRepairReport,
    StudyRepairRequest,
)
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository
from antarest.study.service import (
    MAX_BATCH_DELETE_SIZE,
    MAX_MISSING_STUDY_TIMEOUT,
    IOutputsAccess,
    StudyService,
    StudyUpgraderTask,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import (
    assert_permission,
    assert_permission_on_studies,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import create_raw_study, create_study, create_variant_study, with_admin_user, with_db_context

JWT_USER = JWTUser(id=0, impersonator=0, type="users")


@pytest.fixture
def study_tree(tmp_path: Path) -> Path:
    """
    Create this hierarchy

    tmp_path
    └── workspace1
        └── folder
            ├── studyA
            │   └── study.antares
            ├── studyB
            │   └── study.antares
    """
    workspace = tmp_path / "workspace1"
    c = workspace / "folder/studyA"
    c.mkdir(parents=True)
    (c / "study.antares").touch()

    f = workspace / "folder/studyB"
    f.mkdir(parents=True)
    (f / "study.antares").touch()

    return tmp_path


def with_jwt_user(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
    @wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        with current_user_context(JWT_USER):
            return f(*args, **kwargs)

    return wrapper


def build_study_service(
    raw_study_service: RawStudyService,
    directory_service: DirectoryService,
    repository: StudyMetadataRepository,
    config: Config,
    user_service: LoginService = Mock(spec=LoginService),
    cache_service: ICache = Mock(spec=ICache),
    variant_study_service: VariantStudyService = Mock(spec=VariantStudyService),
    task_service: ITaskService = Mock(spec=ITaskService),
    event_bus: IEventBus = Mock(spec=IEventBus),
) -> StudyService:
    raw_study_service.study_factory = Mock()
    service = StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        directory_service=directory_service,
        command_context=Mock(),
        user_service=user_service,
        repository=repository,
        job_result_repository=Mock(),
        event_bus=event_bus,
        task_service=task_service,
        file_transfer_manager=Mock(),
        cache_service=cache_service,
        config=config,
    )

    class OutputsAccessMock(IOutputsAccess):
        def list_outputs(self, study_id: str) -> list[OutputMetadata]:
            return []

        def get_outputs_details(self, study_id: str) -> dict[str, Simulation]:
            return {}

        def copy_output(self, src_study_id: str, target_study_id: str, output_id: str) -> None:
            pass

        def delete_output(self, study_id: str, output_id: str) -> None:
            pass

        def archive_output(self, study_id: str, output_id: str) -> None:
            pass

        def write_output_to_dir(self, study_id: str, output_id: str, parent_dir: Path) -> None:
            pass

    service.register_output_access(OutputsAccessMock())
    return service


def study_to_dto(study: Study, folder_path: t.Optional[str] = None) -> StudyMetadataDTO:
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
        horizon=study.horizon,
        scenario=None,
        status=None,
        doc=None,
        folder=folder_path,
    )


def fill_study_service_with_command_context(study_service: StudyService, command_context: CommandContext) -> None:
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.command_factory = Mock(spec=CommandFactory)
    variant_study_service.command_factory.command_context = command_context
    study_service.storage_service.variant_study_service = variant_study_service


def test_study_listing(db_session: Session) -> None:
    bob = User(id=2, name="bob")
    alice = User(id=3, name="alice")

    study_version = "810"
    a = create_raw_study(
        id="A",
        owner=bob,
        type="rawstudy",
        name="A",
        version=study_version,
        created_at=current_time(),
        updated_at=current_time(),
        path="",
        workspace=DEFAULT_WORKSPACE_NAME,
    )
    b = create_raw_study(
        id="B",
        owner=alice,
        type="rawstudy",
        name="B",
        version=study_version,
        created_at=current_time(),
        updated_at=current_time(),
        path="",
        workspace="other",
    )
    c = create_raw_study(
        id="C",
        owner=bob,
        type="rawstudy",
        name="C",
        version=study_version,
        created_at=current_time(),
        updated_at=current_time(),
        path="",
        workspace="other2",
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
    service = build_study_service(
        raw_study_service, Mock(spec=DirectoryService), repository, config, cache_service=cache
    )
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


def test_sync_studies_from_disk() -> None:
    now = current_time()

    # Studies in DB
    ma = create_raw_study(id="a", path="a", workspace="workspace1")
    mb = create_raw_study(id="b", path="b", workspace="workspace1")
    mc = create_raw_study(
        id="c",
        path="c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace="workspace1",
        owner=User(id=0),
    )
    md = create_raw_study(
        id="d",
        path="d",
        missing=current_time() - timedelta(MAX_MISSING_STUDY_TIMEOUT + 1),
        workspace="workspace1",
    )
    me = create_raw_study(
        id="e",
        path="e",
        folder="e",
        name="e",
        created_at=now,
        missing=current_time() - timedelta(MAX_MISSING_STUDY_TIMEOUT - 1),
        workspace="workspace1",
    )
    mg = create_raw_study(
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
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config)

    # call function with scanned folders
    service.sync_studies_on_disk([fa, fa2, fc, fe, ff, ff2])

    # here d exists in DB but not on disc so it should be removed
    repository.delete.assert_called_once_with(md.id)
    # (f, workspace1) exist on disc but not in DB so it should be added
    # The studies a and f exists in workspace 2, studies under the same path exists in workspace 1,
    # we check that we indeed save them in DB
    # (f, workspace1) exist on disc but not in DB so it should be added
    # The studies a and f exists in workspace 2, studies under the same path exists in workspace 1,
    # we check that we indeed save them in DB
    saved_studies_map = {(s.path, s.workspace): s for s in [c.args[0] for c in repository.save.call_args_list]}
    assert len(saved_studies_map) == 5

    # study 'b' is in DB but not on disk, so it should be marked as missing
    study_b = saved_studies_map[("b", "workspace1")]
    assert study_b.id == "b"
    assert study_b.missing is not None

    # study 'e' was missing and re-appeared, so it should be restored
    study_e = saved_studies_map[("e", "workspace1")]
    assert study_e.id == "e"
    assert study_e.missing is None
    assert study_e.created_at == now

    # new studies should be added
    study_a2 = saved_studies_map[("a", "workspace2")]
    assert study_a2.name == "a"
    assert study_a2.public_mode == PublicMode.FULL

    study_f1 = saved_studies_map[("f", "workspace1")]
    assert study_f1.name == "f"
    assert study_f1.public_mode == PublicMode.FULL

    study_f2 = saved_studies_map[("f", "workspace2")]
    assert study_f2.name == "f"
    assert study_f2.public_mode == PublicMode.FULL


def test_sync_unsuppported_study_from_disk(caplog: LogCaptureFixture) -> None:
    folder_a = StudyFolder(path=Path("a"), workspace="workspace1", groups=[])
    folder_b = StudyFolder(path=Path("b"), workspace="workspace1", groups=[])

    repository = Mock()
    repository.get_all_raw.side_effect = [[]]
    config = Config(storage=StorageConfig(workspaces={"workspace1": WorkspaceConfig()}))
    raw_service = Mock(spec=RawStudyService)
    service = build_study_service(raw_service, Mock(spec=DirectoryService), repository, config)

    def fake_compatibility_check(study: Study) -> None:
        if not hasattr(fake_compatibility_check, "call_count"):
            fake_compatibility_check.call_count = 0

        fake_compatibility_check.call_count += 1

        if fake_compatibility_check.call_count >= 2:
            raise RecursionError("Custom message")

    raw_service.checks_antares_web_compatibility.side_effect = fake_compatibility_check

    with caplog.at_level(level=logging.ERROR):
        service.sync_studies_on_disk([folder_a, folder_b])

    # Ensures the 2nd study wasn't added and went through the mock method
    assert len(caplog.records) == 1
    assert caplog.records[0].msg == "Failed to add study b"
    assert isinstance(caplog.records[0].exc_info[1], RecursionError)

    repository.save.assert_called_once_with(
        RawStudy(
            id=ANY,
            path="a",
            name="a",
            folder="a",
            workspace="workspace1",
            missing=None,
            public_mode=PublicMode.FULL,
        )
    )


# noinspection PyArgumentList
def test_partial_sync_studies_from_disk() -> None:
    now = current_time()
    ma = create_raw_study(id="a", path="a")
    mb = create_raw_study(id="b", path="b")
    mc = create_raw_study(
        id="c",
        path=f"directory{os.sep}c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace="workspace1",
        owner=User(id=0),
    )
    md = create_raw_study(
        id="d",
        path=f"directory{os.sep}d",
        missing=current_time() - timedelta(MAX_MISSING_STUDY_TIMEOUT + 1),
    )
    me = create_raw_study(
        id="e",
        path=f"directory{os.sep}e",
        created_at=now,
        missing=current_time() - timedelta(MAX_MISSING_STUDY_TIMEOUT - 1),
    )
    fc = StudyFolder(path=Path("directory/c"), workspace="workspace1", groups=[])
    fe = StudyFolder(path=Path("directory/e"), workspace="workspace1", groups=[])
    ff = StudyFolder(path=Path("directory/f"), workspace="workspace1", groups=[])

    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, md, me]]
    config = Config(storage=StorageConfig(workspaces={"workspace1": WorkspaceConfig()}))
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config)

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


def test_delete_missing_studies_desktop(study_tree: Path) -> None:
    ma = create_raw_study(id="a", folder="folder/studyA", workspace="workspace1")
    mb = create_raw_study(id="b", folder="folder/studyB", workspace="workspace1")
    mc = create_raw_study(id="c", folder="folder/studyC", workspace="workspace1")
    mc2 = create_raw_study(id="c2", folder="folder/studyC", workspace="workspace2")
    md = create_raw_study(id="managed", folder="managed", workspace="default")

    repository = Mock()
    repository.get_all_raw.side_effect = [[ma, mb, mc, mc2, md]]
    config = Config(
        storage=StorageConfig(
            workspaces={
                "workspace1": WorkspaceConfig(path=study_tree / "workspace1"),
                "workspace2": WorkspaceConfig(path=study_tree / "workspace2"),
            }
        )
    )
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config)

    service.delete_missing_studies()

    repository.delete.assert_called_once_with(mc.id, mc2.id)


@with_db_context
def test_remove_duplicate(db_session: Session) -> None:
    with db_session:
        db_session.add(create_raw_study(id="a", path="/path/to/a"))
        db_session.add(create_raw_study(id="b", path="/path/to/a"))
        db_session.add(create_raw_study(id="c", path="/path/to/c"))
        db_session.commit()
        study_count = db_session.query(RawStudy).filter(RawStudy.path == "/path/to/a").count()
        assert study_count == 2  # there are 2 studies with same path before removing duplicates

    with db_session:
        repository = StudyMetadataRepository(Mock(), db_session)
        config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
        service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config)
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
def test_create_study(tmp_path: Path) -> None:
    # Mock
    repository = Mock()

    # Input
    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    expected = create_raw_study(
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
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=tmp_path)}))
    service = build_study_service(
        study_service, Mock(spec=DirectoryService), repository, config, user_service=user_service
    )
    service.storage_service.variant_study_service.command_factory = Mock()
    service.storage_service.variant_study_service.command_factory.command_context = Mock()
    factory = Mock()
    factory.create_study_dao.return_value = Mock()
    service._study_dao_factories = {StorageMode.FILESYSTEM: factory}

    jwt_user = JWT_USER
    jwt_user.groups = []
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt_user):
            service.create_study("new-study", STUDY_VERSION_7_2, ["my-group"], StorageMode.FILESYSTEM)
    factory.create_study_dao.assert_not_called()

    jwt_user.groups = [JWTGroup(id="my-group", name="group", role=RoleType.WRITER)]
    with current_user_context(jwt_user):
        service.create_study("new-study", STUDY_VERSION_7_2, ["my-group"], StorageMode.FILESYSTEM)

    factory.create_study_dao.assert_called_once()


# noinspection PyArgumentList
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

    user = User(id=0, name="user")
    group = Group(id="my-group", name="group")

    # Expected
    study = create_raw_study(
        id=study_id,
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, Mock(spec=DirectoryService), repository, config)

    study_to_save = create_raw_study(
        id=study_id,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )
    service._save_study(study_to_save)
    repository.save.assert_called_once_with(study)


# noinspection PyArgumentList
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
        Mock(spec=DirectoryService),
        repository,
        config,
        user_service=user_service,
        variant_study_service=variant_study_service,
    )

    study = create_raw_study(id=study_id, owner=alice)
    repository.get.return_value = study
    user_service.get_user.return_value = bob
    service._edit_study_using_command = Mock()

    with current_user_context(jwt_user):
        service.change_owner(study_id, 2)

    service._edit_study_using_command.assert_called_once_with(study=study, url="study/antares/author", data="Bob")
    user_service.get_user.assert_called_once_with(2)
    repository.save.assert_called_with(create_raw_study(id=study_id, owner=bob, last_access=ANY))
    repository.save.assert_called_with(create_raw_study(id=study_id, owner=bob))

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt_user):
            service.change_owner(study_id, 1)


# noinspection PyArgumentList
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
    service = build_study_service(
        Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config, user_service=user_service
    )

    repository.get.return_value = create_study(id=study_id, owner=alice, groups=[group_a])

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(user):
            service.add_group(study_id, "b")

    user.groups.append(group_a_admin)
    user_service.get_group.return_value = group_b
    with current_user_context(user):
        service.add_group(study_id, "b")

    user_service.get_group.assert_called_once_with("b")
    repository.save.assert_called_with(create_study(id=study_id, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = create_study(id=study_id, owner=alice, groups=[group_a, group_b])
    with current_user_context(user):
        service.add_group(study_id, "b")
        user_service.get_group.assert_called_with("b")
    repository.save.assert_called_with(create_study(id=study_id, owner=alice, groups=[group_a, group_b]))

    repository.get.return_value = create_study(id=study_id, owner=alice, groups=[group_a, group_b])
    with current_user_context(user):
        service.remove_group(study_id, "a")
    repository.save.assert_called_with(create_study(id=study_id, owner=alice, groups=[group_b]))


# noinspection PyArgumentList
def test_set_public_mode() -> None:
    study_id = str(uuid.uuid4())
    group_admin = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
    user = JWTUser(id=2, impersonator=2, type="users")

    repository = Mock()
    user_service = Mock()
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(
        Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config, user_service=user_service
    )

    repository.get.return_value = create_study(id=study_id)

    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(user):
            service.set_public_mode(study_id, PublicMode.FULL)

    user.groups.append(group_admin)
    with current_user_context(user):
        service.set_public_mode(study_id, PublicMode.FULL)
    repository.save.assert_called_with(create_study(id=study_id, public_mode=PublicMode.FULL))


# noinspection PyArgumentList
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
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository, config)

    # wrong owner
    repository.get.return_value = create_study(id=study_id, owner=wrong)
    study = service.get_study(study_id)
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.READ)

    # good owner
    study = create_study(id=study_id, owner=good)
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # wrong group
    study = create_study(id=study_id, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.READ)

    # good group
    study = create_study(id=study_id, owner=wrong, groups=[Group(id="my-group")])
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # super admin can do whatever he wants..
    study = create_study(id=study_id)
    with current_user_context(admin):
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)

    # when study found in workspace without group
    study = create_study(id=study_id, public_mode=PublicMode.FULL)
    with pytest.raises(UserHasNotPermissionError):
        with current_user_context(jwt):
            assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
    with current_user_context(jwt):
        assert_permission(study, StudyPermissionType.READ)
        assert_permission(study, StudyPermissionType.WRITE)
        assert_permission(study, StudyPermissionType.RUN)

    # some group roles
    study = create_study(id=study_id, owner=wrong, groups=[Group(id="my-group-2")])
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
        create_study(id=uuid.uuid4(), name="Main Study", owner_id=jwt_users["John"].id, groups=[writers]),
        create_study(id=uuid.uuid4(), name="Variant Study 1", owner_id=jwt_users["Jane"].id, groups=[writers]),
        create_study(id=uuid.uuid4(), name="Variant Study 2", owner_id=jwt_users["Jane"].id, groups=[writers]),
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
        create_study(id=uuid.uuid4(), name="Variant Study 3", owner_id=jwt_users["Jack"].id, groups=[readers, writers])
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
def test_delete_study_calls_callback(tmp_path: Path) -> None:
    study_id = "my_study"
    repository_mock = Mock()
    study_path = tmp_path / study_id
    study_path.mkdir()
    (study_path / "study.antares").touch()
    repository_mock.get.return_value = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=study_path,
        groups=[],
        owner=None,
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
    )
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), repository_mock, Mock())
    callback = Mock()
    service.add_on_deletion_callback(callback)
    service.storage_service.variant_study_service.has_children.return_value = False  # type: ignore

    service.delete_study(study_id, children=False)

    callback.assert_called_once_with(study_id)


@with_admin_user
def test_delete_with_prefetch(tmp_path: Path) -> None:
    study_uuid = str(uuid.uuid4())

    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(Config(), Mock(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(), Mock(), raw_study_service, Mock(), Mock(), variant_study_repository, Mock(), Mock(), Mock()
    )
    # noinspection PyArgumentList
    service = build_study_service(
        raw_study_service,
        Mock(spec=DirectoryService),
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
        last_access=current_time(),
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}
    study_mock.to_enhanced_json_summary.return_value = {
        "id": "my_study",
        "name": "foo",
        "folder": None,
        "workspace": DEFAULT_WORKSPACE_NAME,
    }

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
        last_access=current_time(),
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
    raw_study_service = RawStudyService(Config(), Mock(), Mock(), Mock())
    variant_study_repository = Mock()
    variant_study_service = VariantStudyService(
        Mock(), Mock(), raw_study_service, Mock(), Mock(), variant_study_repository, Mock(), Mock(), Mock()
    )
    service = build_study_service(
        raw_study_service,
        Mock(spec=DirectoryService),
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
    study_mock = create_raw_study(
        archived=False,
        id="my_study",
        path=study_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace=DEFAULT_WORKSPACE_NAME,
        last_access=current_time(),
    )

    v1 = create_variant_study(id="variant_1", path=create_study_fs_mock(variant=True))
    v2 = create_variant_study(id="variant_2", path=create_study_fs_mock(variant=True))
    v3 = create_variant_study(id="sub_variant_1", path=create_study_fs_mock(variant=True))

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
        def __init__(self) -> None:
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
        def __init__(self) -> None:
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


@with_admin_user
def test_delete_raw_study_removes_variant_children(tmp_path: Path) -> None:
    config = Config()

    repository = Mock(spec=StudyMetadataRepository)

    raw_study = create_raw_study(
        id="raw-study",
        path=str(tmp_path / "raw"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    raw_study.to_json_summary = Mock(return_value={"id": raw_study.id})
    raw_study.to_enhanced_json_summary = Mock(return_value={"id": raw_study.id})

    variant_study = create_variant_study(
        id="variant-study",
        path=str(tmp_path / "variant"),
        parent_id=raw_study.id,
        archived=False,
        owner=None,
        groups=[],
    )
    variant_study.generation_task = None
    variant_study.to_json_summary = Mock(return_value={"id": variant_study.id})

    def get_study_by_id(study_id: str) -> Study:
        if study_id == raw_study.id:
            return raw_study
        if study_id == variant_study.id:
            return variant_study
        raise ValueError(f"Unexpected study id: {study_id}")

    repository.get.side_effect = get_study_by_id
    repository.delete = Mock()

    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.delete = Mock()
    raw_study_service.find_archive_path.return_value = str(tmp_path / "archive.zip")

    from typing import Any, Callable

    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.delete = Mock()
    variant_study_service.has_children.side_effect = lambda study: study.id == raw_study.id
    variant_study_service.get_children.return_value = [variant_study]

    def walk_children(
        parent_id: str, fun: Callable[[Any], None], bottom_first: bool, include_parent: bool = True
    ) -> None:
        assert parent_id == raw_study.id
        assert bottom_first is True
        assert include_parent is True
        fun(variant_study)
        if include_parent:
            fun(raw_study)

    variant_study_service.walk_children.side_effect = walk_children

    service = build_study_service(
        raw_study_service=raw_study_service,
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=config,
        variant_study_service=variant_study_service,
    )

    service.delete_study(raw_study.id, children=True)

    variant_study_service.walk_children.assert_called_once()
    args, kwargs = variant_study_service.walk_children.call_args
    assert args[0] == raw_study.id
    assert kwargs.get("bottom_first") is True
    assert kwargs.get("include_parent") is True

    # With delete_studies, repository.delete is called once with all study IDs
    repository.delete.assert_called_once()
    deleted_ids = set(repository.delete.call_args[0])
    assert deleted_ids == {variant_study.id, raw_study.id}


@with_admin_user
def test_delete_studies_raises_when_children_and_no_variants_flag(tmp_path: Path) -> None:
    """Should raise StudyDeletionNotAllowed when study has children and with_variants=False."""
    repository = Mock(spec=StudyMetadataRepository)

    study = create_raw_study(
        id="has-children",
        path=str(tmp_path / "s"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    repository.get.return_value = study

    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.return_value = True

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    with pytest.raises(StudyDeletionNotAllowed):
        service.delete_studies(["has-children"], with_variants=False)

    repository.delete.assert_not_called()


@with_admin_user
def test_delete_studies_also_deletes_child_variants(tmp_path: Path) -> None:
    """Deleting a parent study with with_variants=True also deletes all its child variants."""
    admin_group = Group(id="admin", name="admin")
    repository = Mock(spec=StudyMetadataRepository)

    parent = create_raw_study(
        id="parent",
        path=str(tmp_path / "parent"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    parent.to_json_summary = Mock(return_value={"id": "parent"})
    parent.to_enhanced_json_summary = Mock(return_value={"id": "parent", "workspace": DEFAULT_WORKSPACE_NAME})

    child_variant = create_variant_study(
        id="child-variant",
        path=str(tmp_path / "fv"),
        archived=False,
        owner=None,
        groups=[admin_group],
        public_mode=PublicMode.NONE,
    )
    child_variant.generation_task = None
    child_variant.to_json_summary = Mock(return_value={"id": "child-variant"})

    def get_study(study_id: str) -> Study:
        return {"parent": parent, "child-variant": child_variant}[study_id]

    repository.get.side_effect = get_study
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.side_effect = lambda s: s.id == "parent"

    def walk_children(
        parent_id: str, fun: t.Callable[[t.Any], None], bottom_first: bool, include_parent: bool = True
    ) -> None:
        fun(child_variant)
        if include_parent:
            fun(parent)

    variant_study_service.walk_children.side_effect = walk_children

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    service.delete_studies(["parent"], with_variants=True)
    deleted_ids = set(repository.delete.call_args.args)
    assert "child-variant" in deleted_ids
    assert "parent" in deleted_ids


@with_admin_user
def test_delete_studies_events_pushed_after_db_delete(tmp_path: Path) -> None:
    """Events must be pushed only after repository.delete succeeds."""
    call_order: t.List[str] = []
    repository = Mock(spec=StudyMetadataRepository)
    event_bus = Mock(spec=IEventBus)

    study = create_raw_study(
        id="ev-study",
        path=str(tmp_path / "ev"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    study.to_json_summary = Mock(return_value={"id": "ev-study"})
    study.to_enhanced_json_summary = Mock(return_value={"id": "ev-study", "workspace": DEFAULT_WORKSPACE_NAME})

    repository.get.return_value = study
    repository.delete.side_effect = lambda *args: call_order.append("delete")
    event_bus.push.side_effect = lambda *args: call_order.append("event")
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.return_value = False

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
        event_bus=event_bus,
    )

    service.delete_studies(["ev-study"], with_variants=False)
    assert call_order == ["delete", "event"]


@with_admin_user
def test_delete_studies_empty_list_raises() -> None:
    """Passing an empty list should raise an HTTPException."""
    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=Mock(spec=StudyMetadataRepository),
        config=Config(),
    )

    with pytest.raises(HTTPException):
        service.delete_studies([], with_variants=False)


@with_admin_user
def test_delete_studies_exceeds_max_batch_size() -> None:
    """Exceeding MAX_BATCH_DELETE_SIZE should raise an HTTPException."""
    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=Mock(spec=StudyMetadataRepository),
        config=Config(),
    )

    ids = [f"study-{i}" for i in range(MAX_BATCH_DELETE_SIZE + 1)]
    with pytest.raises(HTTPException):
        service.delete_studies(ids, with_variants=False)


@with_admin_user
def test_delete_studies_runs_callbacks(tmp_path: Path) -> None:
    """Deletion callbacks should be invoked for every deleted study."""
    repository = Mock(spec=StudyMetadataRepository)

    study_a = create_raw_study(
        id="cb-a",
        path=str(tmp_path / "a"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    study_a.to_json_summary = Mock(return_value={"id": "cb-a"})
    study_a.to_enhanced_json_summary = Mock(return_value={"id": "cb-a", "workspace": DEFAULT_WORKSPACE_NAME})

    study_b = create_raw_study(
        id="cb-b",
        path=str(tmp_path / "b"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    study_b.to_json_summary = Mock(return_value={"id": "cb-b"})
    study_b.to_enhanced_json_summary = Mock(return_value={"id": "cb-b", "workspace": DEFAULT_WORKSPACE_NAME})

    def get_study(study_id: str) -> Study:
        return {"cb-a": study_a, "cb-b": study_b}[study_id]

    repository.get.side_effect = get_study
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.return_value = False

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    callback = Mock()
    service.add_on_deletion_callback(callback)
    service.delete_studies(["cb-a", "cb-b"], with_variants=False)
    assert callback.call_count == 2
    callback_ids = {c.args[0] for c in callback.call_args_list}
    assert callback_ids == {"cb-a", "cb-b"}


def test_delete_studies_no_permission_on_one_study(tmp_path: Path) -> None:
    """When user lacks WRITE permission on one study, the whole batch must fail."""
    # Non-admin user who owns study-a but not study-b
    user = JWTUser(id=99, impersonator=99, type="users", groups=[])
    repository = Mock(spec=StudyMetadataRepository)

    study_a = create_raw_study(
        id="study-a",
        path=str(tmp_path / "a"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=99, name="owner"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    study_b = create_raw_study(
        id="study-b",
        path=str(tmp_path / "b"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=50, name="other"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    def get_study(study_id: str) -> Study:
        return {"study-a": study_a, "study-b": study_b}[study_id]

    repository.get.side_effect = get_study
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.return_value = False

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    with current_user_context(user):
        with pytest.raises(UserHasNotPermissionError):
            service.delete_studies(["study-a", "study-b"], with_variants=False)

    # Nothing should be deleted because the batch failed early
    repository.delete.assert_not_called()


def test_delete_studies_no_permission_on_variant(tmp_path: Path) -> None:
    """When user lacks WRITE on a variant child, the batch must fail."""
    user = JWTUser(id=99, impersonator=99, type="users", groups=[])
    repository = Mock(spec=StudyMetadataRepository)

    parent = create_raw_study(
        id="parent",
        path=str(tmp_path / "parent"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=99, name="owner"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    # Variant permission should be denied (different owner)
    variant = create_variant_study(
        id="child-variant",
        path=str(tmp_path / "variant"),
        parent_id="parent",
        archived=False,
        owner=User(id=50, name="other"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    variant.generation_task = None

    def get_study(study_id: str) -> Study:
        return {"parent": parent, "child-variant": variant}[study_id]

    repository.get.side_effect = get_study
    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.side_effect = lambda s: s.id == "parent"

    def walk_children(
        parent_id: str, fun: t.Callable[[t.Any], None], bottom_first: bool, include_parent: bool = True
    ) -> None:
        fun(variant)
        if include_parent:
            fun(parent)

    variant_study_service.walk_children.side_effect = walk_children

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    with current_user_context(user):
        with pytest.raises(UserHasNotPermissionError):
            service.delete_studies(["parent"], with_variants=True)

    # Permission failure on the variant must prevent any deletion
    repository.delete.assert_not_called()


@with_admin_user
def test_delete_studies_invalid_id(tmp_path: Path) -> None:
    """When one study ID does not exist, the batch must fail with StudyNotFoundError."""
    repository = Mock(spec=StudyMetadataRepository)

    study_a = create_raw_study(
        id="study-a",
        path=str(tmp_path / "a"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )

    def get_study(study_id: str) -> t.Optional[Study]:
        if study_id == "study-a":
            return study_a
        return None  # Simulates missing study

    repository.get.side_effect = get_study

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
    )

    with pytest.raises(StudyNotFoundError):
        service.delete_studies(["study-a", "nonexistent-id"], with_variants=False)

    repository.delete.assert_not_called()


@with_admin_user
def test_delete_studies_duplicate_ids(tmp_path: Path) -> None:
    """Duplicate IDs in the list should be deduplicated — study deleted and notified once."""
    repository = Mock(spec=StudyMetadataRepository)
    event_bus = Mock(spec=IEventBus)

    study = create_raw_study(
        id="dup-study",
        path=str(tmp_path / "dup"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    study.to_json_summary = Mock(return_value={"id": "dup-study"})
    study.to_enhanced_json_summary = Mock(return_value={"id": "dup-study", "workspace": DEFAULT_WORKSPACE_NAME})

    repository.get.return_value = study

    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.return_value = False

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
        event_bus=event_bus,
    )

    service.delete_studies(["dup-study", "dup-study"], with_variants=False)

    # Deduplicated — only one delete call and one event
    repository.delete.assert_called_once_with("dup-study")
    assert event_bus.push.call_count == 1


@with_admin_user
def test_delete_studies_variant_id_also_in_list(tmp_path: Path) -> None:
    """When a variant ID is explicitly listed alongside its parent, it must not be deleted twice."""
    repository = Mock(spec=StudyMetadataRepository)
    event_bus = Mock(spec=IEventBus)

    parent = create_raw_study(
        id="parent",
        path=str(tmp_path / "parent"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=None,
        groups=[],
    )
    parent.to_json_summary = Mock(return_value={"id": "parent"})
    parent.to_enhanced_json_summary = Mock(return_value={"id": "parent", "workspace": DEFAULT_WORKSPACE_NAME})

    variant = create_variant_study(
        id="child-variant",
        path=str(tmp_path / "variant"),
        parent_id="parent",
        archived=False,
        owner=None,
        groups=[],
    )
    variant.generation_task = None
    variant.to_json_summary = Mock(return_value={"id": "child-variant"})

    def get_study(study_id: str) -> Study:
        return {"parent": parent, "child-variant": variant}[study_id]

    repository.get.side_effect = get_study

    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.has_children.side_effect = lambda s: s.id == "parent"

    def walk_children(
        parent_id: str, fun: t.Callable[[t.Any], None], bottom_first: bool, include_parent: bool = True
    ) -> None:
        fun(variant)
        if include_parent:
            fun(parent)

    variant_study_service.walk_children.side_effect = walk_children

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
        event_bus=event_bus,
    )

    # Both parent and its child-variant are passed explicitly
    service.delete_studies(["parent", "child-variant"], with_variants=True)

    # Should still result in a single delete call with no duplicate IDs
    repository.delete.assert_called_once()
    deleted_ids = list(repository.delete.call_args.args)
    assert sorted(deleted_ids) == ["child-variant", "parent"]


def test_move_variant_study_is_forbidden(tmp_path: Path) -> None:
    repository = Mock(spec=StudyMetadataRepository)
    variant = create_variant_study(
        id="child-variant",
        path=str(tmp_path / "variant"),
        parent_id="parent",
        archived=False,
        owner=User(id=99, name="owner"),
        groups=[],
        public_mode=PublicMode.NONE,
    )
    repository.get.return_value = variant

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Config(),
    )

    with current_user_context(JWTUser(id=99, impersonator=99, type="users", groups=[])):
        with pytest.raises(UnsupportedOperationOnThisStudyType):
            service.move_study("child-variant", "folder")

    repository.save.assert_not_called()


def test_move_raw_study_fails_without_write_access_on_variant_children(tmp_path: Path) -> None:
    user = JWTUser(id=99, impersonator=99, type="users", groups=[])
    repository = Mock(spec=StudyMetadataRepository)
    directory_service = Mock(spec=DirectoryService)

    parent = create_raw_study(
        id="parent",
        path=str(tmp_path / "parent"),
        archived=False,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=99, name="owner"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    variant = create_variant_study(
        id="child-variant",
        path=str(tmp_path / "variant"),
        parent_id="parent",
        archived=False,
        owner=User(id=50, name="other"),
        groups=[],
        public_mode=PublicMode.NONE,
    )

    repository.get.return_value = parent

    variant_study_service = Mock(spec=VariantStudyService)
    variant_study_service.repository = Mock()
    variant_study_service.repository.get_all_descendants.return_value = [variant]

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=directory_service,
        repository=repository,
        config=Config(),
        variant_study_service=variant_study_service,
    )

    with current_user_context(user):
        with pytest.raises(UserHasNotPermissionError):
            service.move_study("parent", "folder")

    repository.save.assert_not_called()
    directory_service.get_directory_by_path.assert_not_called()


@pytest.mark.parametrize(
    "tree_node,url,data,expected_name",
    [
        (Mock(spec=IniFileNode), "url", 0, "update_config"),
        (Mock(spec=InputSeriesMatrix), "url", [[0]], "replace_matrix"),
        (Mock(spec=RawFileNode), "comments", "0", "replace_comments"),
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
        blob_service=Mock(spec=BlobService),
    )

    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
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
def test_task_upgrade_study(tmp_path: Path) -> None:
    service = build_study_service(
        raw_study_service=Mock(spec=RawStudyService),
        directory_service=Mock(spec=DirectoryService),
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
                name=f"Upgrade study my_study ({study_id}) to version 8",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(current_time()),
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
        f"Upgrade study my_study ({study_id}) to version 8",
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
@with_admin_user
def test_repair_study__archive_consistency__dry_run(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    archive_path = tmp_path / f"{study_id}.7z"
    archive_path.touch()

    now = current_time()
    raw_study = create_raw_study(
        id=study_id,
        name="study_to_repair",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path / "missing-study"),
        created_at=now,
        updated_at=now,
        archived=False,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
    )

    db.session.add(raw_study)
    db.session.commit()

    cache_service = Mock()
    repository = StudyMetadataRepository(cache_service)
    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.find_archive_path.return_value = archive_path
    task_service = Mock(spec=ITaskService)
    event_bus = Mock(spec=IEventBus)
    service = build_study_service(
        raw_study_service=raw_study_service,
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Mock(),
        cache_service=cache_service,
        task_service=task_service,
        event_bus=event_bus,
    )

    captured_task = {}

    def add_task_side_effect(
        callback: t.Any,
        name: str,
        task_type: TaskType,
        ref_id: str,
        progress: int | None,
        custom_event_messages: t.Any,
    ) -> str:
        captured_task["callback"] = callback
        captured_task["name"] = name
        captured_task["task_type"] = task_type
        captured_task["ref_id"] = ref_id
        return "repair-task-id"

    task_service.add_task.side_effect = add_task_side_effect

    task_id = service.repair_study(study_id, StudyRepairRequest())

    assert task_id == "repair-task-id"
    assert captured_task["task_type"] == TaskType.REPAIR_STUDY
    result = captured_task["callback"](Mock())
    report = StudyRepairReport.model_validate_json(result.return_value)

    db.session.expire_all()
    repaired_study = db.session.get(Study, study_id)
    assert repaired_study is not None
    assert not repaired_study.archived
    assert len(report.issues) == 1
    assert report.proposed_actions[0].code == "set_archived_true"
    assert report.applied_actions == []
    event_bus.push.assert_not_called()


@with_db_context
@with_admin_user
def test_repair_study__archive_consistency__apply(tmp_path: Path) -> None:
    study_id = str(uuid.uuid4())
    archive_path = tmp_path / f"{study_id}.7z"
    archive_path.touch()

    now = current_time()
    raw_study = create_raw_study(
        id=study_id,
        name="study_to_repair",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path / "missing-study"),
        created_at=now,
        updated_at=now,
        archived=False,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
    )

    db.session.add(raw_study)
    db.session.commit()

    cache_service = Mock()
    repository = StudyMetadataRepository(cache_service)
    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.find_archive_path.return_value = archive_path
    task_service = Mock(spec=ITaskService)
    event_bus = Mock(spec=IEventBus)
    service = build_study_service(
        raw_study_service=raw_study_service,
        directory_service=Mock(spec=DirectoryService),
        repository=repository,
        config=Mock(),
        cache_service=cache_service,
        task_service=task_service,
        event_bus=event_bus,
    )

    captured_task = {}

    def add_task_side_effect(
        callback: t.Any,
        name: str,
        task_type: TaskType,
        ref_id: str,
        progress: int | None,
        custom_event_messages: t.Any,
    ) -> str:
        captured_task["callback"] = callback
        return "repair-task-id"

    task_service.add_task.side_effect = add_task_side_effect

    service.repair_study(study_id, StudyRepairRequest(dry_run=False))

    result = captured_task["callback"](Mock())
    report = StudyRepairReport.model_validate_json(result.return_value)

    db.session.expire_all()
    repaired_study = db.session.get(Study, study_id)
    assert repaired_study is not None
    assert repaired_study.archived
    assert report.applied_actions[0].code == "set_archived_true"
    event_bus.push.assert_called_once()


@with_jwt_user
def test_repair_study__forbidden() -> None:
    service = build_study_service(Mock(spec=RawStudyService), Mock(spec=DirectoryService), Mock(), Mock())

    with pytest.raises(UserHasNotPermissionError):
        service.repair_study("study-id", StudyRepairRequest())


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
    now = current_time()
    raw_study = create_raw_study(
        id=study_id,
        name=study_name,
        workspace=workspace,
        path=str(tmp_path),
        created_at=now,
        updated_at=now,
        version=current_version,
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
    parsed_target_version = StudyVersion.parse(target_version)
    task = StudyUpgraderTask(
        study_id,
        parsed_target_version,
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
    actual_study: RawStudy = db.session.get(Study, study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == f"{parsed_target_version:2d}"

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
    assert actual.message == f"Successfully upgraded study '{study_id}' to version 8"


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
    now = current_time()
    raw_study = create_raw_study(
        id=study_id,
        name=study_name,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path),
        created_at=now,
        updated_at=now,
        version=old_version,
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
    actual_study: RawStudy = db.session.get(Study, study_id)
    assert actual_study is not None, "Not in database"
    assert actual_study.version == old_version

    # No event must be emitted
    event_bus.push.assert_not_called()
