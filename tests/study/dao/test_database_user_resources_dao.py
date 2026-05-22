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
from pathlib import PurePosixPath

import pytest

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.core.exceptions import UserResourcesNotFound
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_save_user_resources_file(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id = blob_service.save(b"test content")
    dao.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id=blob_id)]
    )

    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].path == PurePosixPath("file_path")
    assert result[0].resource_type == ResourceType.FILE
    assert result[0].blob_id == blob_id

    dao.delete_user_resource(PurePosixPath("file_path"))

    assert len(list(dao.get_all_user_resources())) == 0


def test_save_user_resources_folder(dao: StudyDao) -> None:
    dao.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("folder_path"), resource_type=ResourceType.FOLDER)]
    )
    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].path == PurePosixPath("folder_path")
    assert result[0].resource_type == ResourceType.FOLDER
    assert result[0].blob_id is None


def test_update_blob_id(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id = blob_service.save(b"initial content")
    resource = UserResourceDataCreation(
        path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id=blob_id
    )
    dao.save_user_resources([resource])

    updated_blob_id = blob_service.save(b"updated content")
    updated_resource = UserResourceDataCreation(
        path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id=updated_blob_id
    )
    dao.save_user_resources([updated_resource])

    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].blob_id == updated_blob_id


def test_user_resources_not_exists(db_dao: DatabaseStudyDao) -> None:
    with pytest.raises(UserResourcesNotFound):
        db_dao.delete_user_resource(PurePosixPath("file_path"))


def test_save_user_resources_folder_with_file(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id = blob_service.save(b"inside content")
    dao.save_user_resources(
        [
            UserResourceDataCreation(path=PurePosixPath("empty_folder_path"), resource_type=ResourceType.FOLDER),
            UserResourceDataCreation(
                path=PurePosixPath("folder_path/inside.txt"), resource_type=ResourceType.FILE, blob_id=blob_id
            ),
        ]
    )
    result = sorted(dao.get_all_user_resources(), key=lambda r: str(r.path))
    assert len(result) == 2
    assert result[0].path == PurePosixPath("empty_folder_path")
    assert result[0].resource_type == ResourceType.FOLDER
    assert result[0].blob_id is None
    assert result[1].path == PurePosixPath("folder_path/inside.txt")
    assert result[1].resource_type == ResourceType.FILE
    assert result[1].blob_id == blob_id
