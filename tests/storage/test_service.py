from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.login.model import User, Role
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.model import Metadata
from antarest.storage.service import StorageService, UserHasNotPermissionError
from antarest.storage.web.exceptions import StudyNotFoundError


def test_get_studies_uuid():
    bob = User(id=1, name="bob")
    alice = User(id=2, name="alice")

    # Mock
    repository = Mock()
    repository.get.side_effect = [
        Metadata(id="A", users=[bob]),
        Metadata(id="B", users=[alice]),
        Metadata(id="C", users=[bob]),
    ]

    study_service = Mock()
    study_service.get_study_uuids.return_value = ["A", "B", "C"]

    service = StorageService(
        study_service=study_service,
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
    )

    studies = service._get_study_uuids(StorageServiceParameters(user=bob))

    assert ["A", "C"] == studies


def test_import():
    # Mock
    repository = Mock()

    uuid = str(uuid4())
    importer = Mock()
    importer.import_study.return_value = uuid

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
    params = StorageServiceParameters(
        user=User(id=0, name="user", role=Role.USER)
    )

    # Expected
    metadata = Metadata(
        id=uuid,
        name="CAPTION",
        version="VERSION",
        author="AUTHOR",
        created_at=datetime.fromtimestamp(1234),
        updated_at=datetime.fromtimestamp(9876),
        users=[params.user],
    )

    service = StorageService(
        study_service=study_service,
        importer_service=importer,
        exporter_service=Mock(),
        repository=repository,
    )

    assert uuid == service.import_study(stream=None, params=params)
    repository.save.assert_called_once_with(metadata)


def test_check_user_permission():
    uuid = str(uuid4())
    user = User(id=0)

    repository = Mock()

    service = StorageService(
        study_service=Mock(),
        importer_service=Mock(),
        exporter_service=Mock(),
        repository=repository,
    )

    repository.get.return_value = None
    with pytest.raises(StudyNotFoundError):
        service._check_user_permission(user, uuid)
    assert not service._check_user_permission(user, uuid, raising=False)

    repository.get.return_value = Metadata(id=uuid, users=[])
    with pytest.raises(UserHasNotPermissionError):
        service._check_user_permission(user, uuid)
    assert not service._check_user_permission(user, uuid, raising=False)

    repository.get.return_value = Metadata(id=uuid, users=[user])
    assert service._check_user_permission(user, uuid)
