from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from antarest.login.model import User, Role, Group
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.model import Metadata, StudyContentStatus, StudyFolder
from antarest.storage.service import StorageService, UserHasNotPermissionError


def test_get_studies_uuid() -> None:
    bob = User(id=1, name="bob")
    alice = User(id=2, name="alice")

    a = Metadata(id="A", owner=bob)
    b = Metadata(id="B", owner=alice)
    c = Metadata(id="C", owner=bob)

    # Mock
    repository = Mock()
    repository.get_all.return_value = [a, b, c]

    study_service = Mock()

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    studies = service._get_study_metadatas(RequestParameters(user=bob))

    assert [a, c] == studies


def test_sync_studies_from_disk() -> None:
    ma = Metadata(id="a", path="a")
    fa = StudyFolder(path=Path("a"), workspace="", groups=[])
    mb = Metadata(id="b", path="b")
    mc = Metadata(
        id="c",
        path="c",
        name="c",
        content_status=StudyContentStatus.WARNING,
        workspace="default",
        owner=User(id=0),
    )
    fc = StudyFolder(path=Path("c"), workspace="default", groups=[])

    repository = Mock()
    repository.get_all.side_effect = [[ma, mb], [ma]]

    service = StorageService(
        study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    service.sync_studies_on_disk([fa, fc])

    repository.delete.assert_called_once_with(mb.id)
    repository.save.assert_called_once()


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
    user = User(id=0, name="user", role=Role.USER)
    group = Group(id="my-group", name="group")

    # Expected
    metadata = Metadata(
        id=uuid,
        name="CAPTION",
        version="VERSION",
        author="AUTHOR",
        created_at=datetime.fromtimestamp(1234),
        updated_at=datetime.fromtimestamp(9876),
        content_status=StudyContentStatus.VALID,
        workspace="default",
        owner=user,
        groups=[group],
    )

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    service._save_metadata(
        Metadata(id=uuid, workspace="default"), owner=user, group=group
    )
    repository.save.assert_called_once_with(metadata)


def test_assert_permission() -> None:
    uuid = str(uuid4())
    group = Group(id="my-group")
    good = User(id=0, groups=[group])
    wrong = User(id=2)

    repository = Mock()

    service = StorageService(
        study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
        event_bus=Mock(),
    )

    # wrong owner
    repository.get.return_value = Metadata(id=uuid, owner=wrong)
    md = service._get_metadata(uuid)
    with pytest.raises(UserHasNotPermissionError):
        service._assert_permission(good, md)
    assert not service._assert_permission(good, md, raising=False)

    # good owner
    md = Metadata(id=uuid, owner=good)
    assert service._assert_permission(good, md)

    # wrong group
    md = Metadata(id=uuid, owner=wrong, groups=[Group(id="wrong")])
    with pytest.raises(UserHasNotPermissionError):
        service._assert_permission(good, md)
    assert not service._assert_permission(good, md, raising=False)

    # good group
    md = Metadata(id=uuid, owner=wrong, groups=[group])
    assert service._assert_permission(good, md)
