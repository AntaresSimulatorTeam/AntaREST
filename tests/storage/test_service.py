from datetime import datetime
from pathlib import Path
from typing import Union
from unittest.mock import Mock, seal
from uuid import uuid4

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.jwt import JWTUser, JWTGroup, DEFAULT_ADMIN_USER
from antarest.core.model import JSON, SUB_JSON
from antarest.core.permissions import (
    StudyPermissionType,
)
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.roles import RoleType
from antarest.login.model import User, Group, GroupDTO
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
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
    StudyDownloadType,
    StudyMetadataDTO,
    OwnerInfo,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService, UserHasNotPermissionError
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
    Simulation,
    Link,
    Set,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import assert_permission
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


def build_study_service(
    raw_study_service: RawStudyService,
    repository: StudyMetadataRepository,
    config: Config,
    user_service: LoginService = Mock(),
    cache_service: ICache = Mock(),
    variant_study_service=Mock(),
) -> StudyService:
    return StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        user_service=user_service,
        repository=repository,
        event_bus=Mock(),
        task_service=Mock(),
        cache_service=cache_service,
        config=config,
    )


@pytest.mark.unit_test
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
    service = build_study_service(study_service, repository, config)

    studies = service._get_study_metadatas(
        RequestParameters(user=JWTUser(id=1, impersonator=1, type="users"))
    )

    assert [a, c] == studies


def study_to_dto(study: Study, summary: bool) -> StudyMetadataDTO:
    return StudyMetadataDTO(
        id=study.id,
        name=study.name,
        version=int(study.version),
        created=study.created_at.timestamp(),
        updated=study.updated_at.timestamp(),
        workspace=DEFAULT_WORKSPACE_NAME,
        managed=True,
        type=study.type,
        archived=study.archived if study.archived is not None else False,
        owner=OwnerInfo(id=study.owner.id, name=study.owner.name)
        if study.owner is not None
        else OwnerInfo(name="Unknown"),
        groups=[
            GroupDTO(id=group.id, name=group.name) for group in study.groups
        ],
        public_mode=study.public_mode or PublicMode.NONE,
        horizon=None,
        scenario=None,
        status=None,
        doc=None,
        folder=None,
    )


@pytest.mark.unit_test
def test_study_listing() -> None:
    bob = User(id=1, name="bob")
    alice = User(id=2, name="alice")

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
    )

    # Mock
    repository = Mock()
    repository.get_all.return_value = [a, b, c]

    raw_study_service = Mock(spec=RawStudyService)
    raw_study_service.get_study_information.side_effect = study_to_dto

    cache = Mock(spec=ICache)
    cache.get.return_value = None

    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(
        raw_study_service, repository, config, cache_service=cache
    )

    studies = service.get_studies_information(
        True,
        False,
        RequestParameters(user=JWTUser(id=1, impersonator=1, type="users")),
    )

    expected_result = {
        e.id: e for e in map(lambda x: study_to_dto(x, True), [a, c])
    }
    assert expected_result == studies
    cache.get.return_value = {
        e.id: e for e in map(lambda x: study_to_dto(x, True), [a, b, c])
    }

    studies = service.get_studies_information(
        True,
        False,
        RequestParameters(user=JWTUser(id=1, impersonator=1, type="users")),
    )

    assert expected_result == studies
    cache.put.assert_called_once()

    cache.get.return_value = None
    studies = service.get_studies_information(
        True,
        True,
        RequestParameters(user=JWTUser(id=1, impersonator=1, type="users")),
    )

    expected_result = {
        e.id: e for e in map(lambda x: study_to_dto(x, True), [a])
    }
    assert expected_result == studies


@pytest.mark.unit_test
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
    service = build_study_service(Mock(), repository, config)

    service.sync_studies_on_disk([fa, fc])

    repository.delete.assert_called_once_with(mb.id)
    repository.save.assert_called_once()


@pytest.mark.unit_test
def test_remove_duplicate() -> None:
    ma = RawStudy(id="a", path="a")
    mb = RawStudy(id="b", path="a")

    repository = Mock()
    repository.get_all.return_value = [ma, mb]
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(Mock(), repository, config)

    service.remove_duplicates()
    repository.delete.assert_called_once_with(mb.id)


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
        created_at=datetime.fromtimestamp(1234),
        updated_at=datetime.fromtimestamp(9876),
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
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(
        study_service, repository, config, user_service=user_service
    )

    with pytest.raises(UserHasNotPermissionError):
        service.create_study(
            "new-study",
            720,
            ["my-group"],
            RequestParameters(JWTUser(id=0, impersonator=0, type="users")),
        )

    service.create_study(
        "new-study",
        720,
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
    service = build_study_service(study_service, repository, config)

    service._save_study(
        RawStudy(id=uuid, workspace=DEFAULT_WORKSPACE_NAME),
        owner=jwt,
    )
    repository.save.assert_called_once_with(study)


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
    service = build_study_service(study_service, repository, config)

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
    input_data.type = StudyDownloadType.LINK
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
    input_data.type = StudyDownloadType.DISTRICT
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


@pytest.mark.unit_test
def test_change_owner() -> None:
    uuid = str(uuid4())
    alice = User(id=1)
    bob = User(id=2, name="Bob")

    mock_file_study = Mock()
    mock_file_study.tree.get_node.return_value = Mock(spec=IniFileNode)

    repository = Mock()
    user_service = Mock()
    study_service = Mock(spec=RawStudyService)
    study_service.get_raw.return_value = mock_file_study
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(
        study_service, repository, config, user_service=user_service
    )
    service.variant_study_service.command_factory.command_context = Mock(
        spec=CommandContext
    )

    study = RawStudy(id=uuid, owner=alice)
    repository.get.return_value = study
    user_service.get_user.return_value = bob
    service._edit_study_using_command = Mock()

    service.change_owner(
        uuid, 2, RequestParameters(JWTUser(id=1, impersonator=1, type="users"))
    )
    user_service.get_user.assert_called_once_with(
        2, RequestParameters(JWTUser(id=1, impersonator=1, type="users"))
    )
    repository.save.assert_called_once_with(RawStudy(id=uuid, owner=bob))

    service._edit_study_using_command.assert_called_once_with(
        study=study, url="study/antares/author", data="Bob"
    )

    with pytest.raises(UserHasNotPermissionError):
        service.change_owner(
            uuid,
            1,
            RequestParameters(JWTUser(id=1, impersonator=1, type="users")),
        )


@pytest.mark.unit_test
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
    service = build_study_service(
        Mock(), repository, config, user_service=user_service
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


@pytest.mark.unit_test
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
    service = build_study_service(
        Mock(), repository, config, user_service=user_service
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


@pytest.mark.unit_test
def test_check_errors():
    study_service = Mock()
    study_service.check_errors.return_value = ["Hello", "World"]

    study = RawStudy(id="hello world")
    repo = Mock()
    repo.get.return_value = study
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(study_service, repo, config)

    assert ["Hello", "World"] == service.check_errors("hello world")
    study_service.check_errors.assert_called_once_with(study)
    repo.get.assert_called_once_with("hello world")


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
    config = Config(
        storage=StorageConfig(
            workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
        )
    )
    service = build_study_service(Mock(), repository, config)

    # wrong owner
    repository.get.return_value = Study(id=uuid, owner=wrong)
    study = service.get_study(uuid)
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

    service.delete_study(
        study_uuid,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    callback.assert_called_once_with(study_uuid)


@pytest.mark.unit_test
def test_delete_with_prefetch(tmp_path: Path):
    study_uuid = "my_study"

    study_metadata_repository = Mock()
    raw_study_service = RawStudyService(
        Config(), Mock(), Mock(), Mock(), Mock()
    )
    variant_study_service = VariantStudyService(
        Mock(),
        Mock(),
        raw_study_service,
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
    )
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
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    study_metadata_repository.get.return_value = study_mock

    # if this fails, it may means the study metadata mock is missing some attribute definition
    # this test is here to prevent errors if we add attribute fetching from child classes (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
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
    )
    study_mock.to_json_summary.return_value = {"id": "my_study", "name": "foo"}

    # it freezes the mock and raise Attribute error if anything else than defined is used
    seal(study_mock)

    study_metadata_repository.get.return_value = study_mock

    # if this fails, it may means the study metadata mock is missing some definition
    # this test is here to prevent errors if we add attribute fetching from child classes (attributes in polymorphism are lazy)
    # see the comment in the delete method for more information
    service.delete_study(
        study_uuid,
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
    service._get_study_storage_service = Mock(return_value=study_service)

    service._edit_study_using_command(study=Mock(), url="", data=[])
    command.apply.assert_called_with(file_study)

    study_service = Mock(spec=VariantStudyService)
    study_service.get_raw.return_value = file_study
    service._get_study_storage_service = Mock(return_value=study_service)
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

    service.variant_study_service.command_factory.command_context = (
        command_context
    )

    command = service._create_edit_study_command(
        tree_node=tree_node, url=url, data=data
    )

    assert command.command_name.value == expected_name
