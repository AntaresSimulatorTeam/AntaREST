from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.login.model import User, Group
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.business.permissions import StudyPermissionType
from antarest.storage.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
)
from antarest.storage.service import StorageService, UserHasNotPermissionError


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

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    studies = service._get_study_metadatas(
        RequestParameters(user=JWTUser(id=1))
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

    service = StorageService(
        study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
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
    study_service.create_study.return_value = expected

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    service.create_study("new-study", RequestParameters(JWTUser(id=0)))

    study_service.create_study.assert_called_once()
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

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    service._save_study(
        RawStudy(id=uuid, workspace=DEFAULT_WORKSPACE_NAME),
        owner=user,
        group=group,
    )
    repository.save.assert_called_once_with(study)


def test_assert_permission() -> None:
    uuid = str(uuid4())
    group = JWTGroup(id="my-group", name="g", role=RoleType.ADMIN)
    jwt = JWTUser(id=0, groups=[group])
    good = User(id=0)
    wrong = User(id=2)

    repository = Mock()

    service = StorageService(
        study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        user_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    # wrong owner
    repository.get.return_value = Study(id=uuid, owner=wrong)
    study = service._get_study(uuid)
    with pytest.raises(UserHasNotPermissionError):
        service._assert_permission(jwt, study, StudyPermissionType.READ)
    assert not service._assert_permission(
        jwt, study, StudyPermissionType.READ, raising=False
    )

    # good owner
    study = Study(id=uuid, owner=good)
    assert service._assert_permission(
        jwt, study, StudyPermissionType.MANAGE_PERMISSIONS
    )

    # wrong group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        service._assert_permission(jwt, study, StudyPermissionType.READ)
    assert not service._assert_permission(
        jwt, study, StudyPermissionType.READ, raising=False
    )

    # good group
    study = Study(id=uuid, owner=wrong, groups=[Group(id="my-group")])
    assert service._assert_permission(
        jwt, study, StudyPermissionType.MANAGE_PERMISSIONS
    )
