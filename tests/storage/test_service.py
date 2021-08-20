from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.roles import RoleType
from antarest.login.model import User, Group
from antarest.core.requests import (
    RequestParameters,
)
from antarest.study.storage.permissions import (
    StudyPermissionType,
    assert_permission,
)
from antarest.study.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    PublicMode,
    StudyDownloadDTO,
    MatrixAggregationResult,
    MatrixIndex,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
    Simulation,
    Link,
    Set,
)
from antarest.study.service import StudyService, UserHasNotPermissionError


def test_get_studies_uuid() -> None:
    bob = User(id=1, name="bob")
    alice = User(id=2, name="alice")

    a = Study(id="A", owner=bob)
    b = Study(id="B", owner=alice)
    c = Study(id="C", owner=bob)

    # Mock
    repository = Mock()
    repository.get_all.return_value = [a, b, c]

    study_service = Mock()
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    studies = service._get_study_metadatas(
        RequestParameters(user=JWTUser(id=1, impersonator=1, type="users"))
    )

    assert [a, c] == studies


def test_sync_studies_from_disk() -> None:
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
    fc = StudyFolder(
        path=Path("c"), workspace=DEFAULT_WORKSPACE_NAME, groups=[]
    )

    repository = Mock()
    repository.get_all.side_effect = [[ma, mb], [ma]]
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=Mock(),
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    service.sync_studies_on_disk([fa, fc])

    repository.delete.assert_called_once_with(mb.id)
    repository.save.assert_called_once()


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
        created_at=datetime.fromtimestamp(1234),
        updated_at=datetime.fromtimestamp(9876),
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )

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
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    with pytest.raises(UserHasNotPermissionError):
        service.create_study(
            "new-study",
            ["my-group"],
            RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
        )

    service.create_study(
        "new-study",
        ["my-group"],
        RequestParameters(
            JWTUser(
                id=0,
                impersonator=0,
                type="users",
                groups=[
                    JWTGroup(id="my-group", name="group", role=RoleType.WRITER)
                ],
            )
        ),
    )

    study_service.create.assert_called()
    repository.save.assert_called_once_with(expected)


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
        name="CAPTION",
        version="VERSION",
        author="AUTHOR",
        created_at=datetime.fromtimestamp(1234),
        updated_at=datetime.fromtimestamp(9876),
        content_status=StudyContentStatus.VALID,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=user,
        groups=[group],
    )
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    service._save_study(
        RawStudy(id=uuid, workspace=DEFAULT_WORKSPACE_NAME),
        owner=jwt,
    )
    repository.save.assert_called_once_with(study)


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
    )
    file_config = FileStudyTreeConfig(
        study_path=input_study.path,
        path=input_study.path,
        study_id="",
        version=-1,
        areas={"east": area},
        sets={"north": Set()},
        outputs={"output-id": sim},
        store_new_set=False,
    )
    study = Mock()

    repository.get.return_value = input_study
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    res_study = {"columns": [["H. VAL|Euro/MWh"]], "data": [[0.5]]}
    study_service.get_raw.return_value = FileStudy(
        config=file_config, tree=study
    )
    study.get.return_value = res_study

    # AREA TYPE
    res_matrix = MatrixAggregationResult(
        index=MatrixIndex(),
        data={"east": {1: {"H. VAL|Euro/MWh": [0.5]}}},
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert result == res_matrix

    # LINK TYPE
    input_data.type = "LINK"
    input_data.filter = ["east>west"]
    res_matrix = MatrixAggregationResult(
        index=MatrixIndex(),
        data={"east^west": {1: {"H. VAL|Euro/MWh": [0.5]}}},
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert result == res_matrix

    # CLUSTER TYPE
    input_data.type = "CLUSTER"
    input_data.filter = []
    input_data.filterIn = "n"
    res_matrix = MatrixAggregationResult(
        index=MatrixIndex(),
        data={"north": {1: {"H. VAL|Euro/MWh": [0.5]}}},
        warnings=[],
    )
    result = service.download_outputs(
        "study-id",
        "output-id",
        input_data,
        RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
    )
    assert result == res_matrix


def test_change_owner() -> None:
    uuid = str(uuid4())
    alice = User(id=1)
    bob = User(id=2, name="Bob")

    repository = Mock()
    user_service = Mock()
    study_service = Mock()
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=user_service,
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    study = RawStudy(id=uuid, owner=alice)
    repository.get.return_value = study
    user_service.get_user.return_value = bob

    service.change_owner(
        uuid, 2, RequestParameters(JWTUser(id=1, impersonator=1, type="users"))
    )
    user_service.get_user.assert_called_once_with(
        2, RequestParameters(JWTUser(id=1, impersonator=1, type="users"))
    )
    repository.save.assert_called_once_with(RawStudy(id=uuid, owner=bob))

    study_service.edit_study.assert_called_once_with(
        study, url="study/antares/author", new="Bob"
    )

    with pytest.raises(UserHasNotPermissionError):
        service.change_owner(
            uuid,
            1,
            RequestParameters(JWTUser(id=1, impersonator=1, type="users")),
        )


def test_manage_group() -> None:
    uuid = str(uuid4())
    alice = User(id=1)
    group_a = Group(id="a", name="Group A")
    group_b = Group(id="b", name="Group B")
    group_a_admin = JWTGroup(id="a", name="Group A", role=RoleType.ADMIN)

    repository = Mock()
    user_service = Mock()
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=Mock(),
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=user_service,
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

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
        RequestParameters(
            JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])
        ),
    )

    user_service.get_group.assert_called_once_with(
        "b",
        RequestParameters(
            JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])
        ),
    )
    repository.save.assert_called_with(
        Study(id=uuid, owner=alice, groups=[group_a, group_b])
    )

    repository.get.return_value = Study(
        id=uuid, owner=alice, groups=[group_a, group_b]
    )
    service.add_group(
        uuid,
        "b",
        RequestParameters(
            JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])
        ),
    )
    user_service.get_group.assert_called_with(
        "b",
        RequestParameters(
            JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])
        ),
    )
    repository.save.assert_called_with(
        Study(id=uuid, owner=alice, groups=[group_a, group_b])
    )

    repository.get.return_value = Study(
        id=uuid, owner=alice, groups=[group_a, group_b]
    )
    service.remove_group(
        uuid,
        "a",
        RequestParameters(
            JWTUser(id=2, impersonator=2, type="users", groups=[group_a_admin])
        ),
    )
    repository.save.assert_called_with(
        Study(id=uuid, owner=alice, groups=[group_b])
    )


def test_set_public_mode() -> None:
    uuid = str(uuid4())
    group_admin = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)

    repository = Mock()
    user_service = Mock()
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=Mock(),
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=user_service,
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    repository.get.return_value = Study(id=uuid)

    with pytest.raises(UserHasNotPermissionError):
        service.set_public_mode(
            uuid,
            PublicMode.FULL,
            RequestParameters(JWTUser(id=1, impersonator=1, type="users")),
        )

    service.set_public_mode(
        uuid,
        PublicMode.FULL,
        RequestParameters(
            JWTUser(id=1, impersonator=1, type="users", groups=[group_admin])
        ),
    )
    repository.save.assert_called_once_with(
        Study(id=uuid, public_mode=PublicMode.FULL)
    )


def test_check_errors():
    study_service = Mock()
    study_service.check_errors.return_value = ["Hello", "World"]

    study = Study(id="hello world")
    repo = Mock()
    repo.get.return_value = study
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=study_service,
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repo,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    assert ["Hello", "World"] == service.check_errors("hello world")
    study_service.check_errors.assert_called_once_with(study)
    repo.get.assert_called_once_with("hello world")


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
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = StudyService(
        raw_study_service=Mock(),
        variant_study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        config=config,
    )

    # wrong owner
    repository.get.return_value = Study(id=uuid, owner=wrong)
    study = service._get_study(uuid)
    with pytest.raises(UserHasNotPermissionError):
        assert_permission(jwt, study, StudyPermissionType.READ)
    assert not assert_permission(
        jwt, study, StudyPermissionType.READ, raising=False
    )

    # good owner
    study = Study(id=uuid, owner=good)
    assert assert_permission(
        jwt, study, StudyPermissionType.MANAGE_PERMISSIONS
    )

    # wrong group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        assert_permission(jwt, study, StudyPermissionType.READ)
    assert not assert_permission(
        jwt, study, StudyPermissionType.READ, raising=False
    )

    # good group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="my-group")])
    assert assert_permission(
        jwt, study, StudyPermissionType.MANAGE_PERMISSIONS
    )

    # super admin can do whatever he wants..
    study = Study(id=uuid)
    assert assert_permission(
        admin, study, StudyPermissionType.MANAGE_PERMISSIONS
    )

    # when study found in workspace without group
    study = Study(id=uuid, public_mode=PublicMode.FULL)
    assert not assert_permission(
        jwt, study, StudyPermissionType.MANAGE_PERMISSIONS, raising=False
    )
    assert assert_permission(jwt, study, StudyPermissionType.DELETE)
    assert assert_permission(jwt, study, StudyPermissionType.READ)
    assert assert_permission(jwt, study, StudyPermissionType.WRITE)
    assert assert_permission(jwt, study, StudyPermissionType.RUN)

    # some group roles
    study = Study(id=uuid, owner=wrong, groups=[Group(id="my-group-2")])
    assert not assert_permission(
        jwt_2, study, StudyPermissionType.WRITE, raising=False
    )
    assert assert_permission(jwt_2, study, StudyPermissionType.READ)
