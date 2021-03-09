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

    # Mock
    repository = Mock()
    repository.get.side_effect = [
        Metadata(id="A", owner=bob),
        Metadata(id="B", owner=alice),
        Metadata(id="C", owner=bob),
    ]

    study_service = Mock()
    study_service.get_study_uuids.return_value = ["A", "B", "C"]

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
    )

    studies = service._get_study_uuids(RequestParameters(user=bob))

    assert ["A", "C"] == studies


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
        owner=user,
        groups=[group],
    )

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
    )

    service._save_metadata(uuid, owner=user, group=group)
    repository.save.assert_called_once_with(metadata)


def test_check_user_permission():
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
    )

    # wrong owner
    repository.get.return_value = Metadata(id=uuid, owner=wrong)
    with pytest.raises(UserHasNotPermissionError):
        service._check_user_permission(good, uuid)
    assert not service._check_user_permission(good, uuid, raising=False)

    # good owner
    repository.get.return_value = Metadata(id=uuid, owner=good)
    assert service._check_user_permission(good, uuid)

    # wrong group
    repository.get.return_value = Metadata(
        id=uuid, owner=wrong, groups=[Group(id="wrong")]
    )
    with pytest.raises(UserHasNotPermissionError):
        service._check_user_permission(good, uuid)
    assert not service._check_user_permission(good, uuid, raising=False)

    # good group
    repository.get.return_value = Metadata(
        id=uuid, owner=wrong, groups=[group]
    )
    assert service._check_user_permission(good, uuid)
