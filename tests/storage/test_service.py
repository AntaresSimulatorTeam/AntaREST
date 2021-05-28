from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.login.model import User, Role, Group
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.model import Metadata, StudyContentStatus
from antarest.storage.service import StorageService, UserHasNotPermissionError


def test_get_studies_uuid():
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


def test_save_metadata():
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


def test_assert_permission():
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
