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
from sqlalchemy import select

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.core.exceptions import UserResourcesNotFound
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE


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

    # Specific DB test. Ensure we only have one entry in DB, as we updated the existing one rather than creating a new.
    if isinstance(dao, DatabaseStudyDao):
        assert len(dao.get_session().execute(select(USER_RESOURCES_TABLE)).all()) == 1

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


def test_deletion_advanced_cases(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id_a = blob_service.save(b"Nice content A !")
    blob_id_b = blob_service.save(b"Nice content B !")
    dao.save_user_resources(
        [
            UserResourceDataCreation(
                path=PurePosixPath("folderA/subfolderA/file.txt"), resource_type=ResourceType.FILE, blob_id=blob_id_a
            ),
            UserResourceDataCreation(
                path=PurePosixPath("folderB/subfolderB/file.txt"), resource_type=ResourceType.FILE, blob_id=blob_id_b
            ),
        ]
    )

    # Delete the folderA. Should delete the subfolderA and the file.txt
    dao.delete_user_resource(PurePosixPath("folderA"))
    assert len(list(dao.get_all_user_resources())) == 1
    assert list(dao.get_all_user_resources())[0].path == PurePosixPath("folderB/subfolderB/file.txt")

    # Delete the file inside folderB. Should delete the file.txt but keep the folder subfolderB
    dao.delete_user_resource(PurePosixPath("folderB/subfolderB/file.txt"))
    user_resources = dao.get_all_user_resources()
    assert len(user_resources) == 1
    assert user_resources[0].path == PurePosixPath("folderB/subfolderB")


def test_save_existing_folder(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id = blob_service.save(b"content")
    dao.save_user_resources(
        [
            UserResourceDataCreation(
                path=PurePosixPath("folderA/subfolderA/file.txt"), resource_type=ResourceType.FILE, blob_id=blob_id
            ),
        ]
    )

    # Saves the folder `folderA/subfolderA`.
    # Should work and be a no-op.
    dao.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("folderA/subfolderA"), resource_type=ResourceType.FOLDER)]
    )

    resources = dao.get_all_user_resources()
    assert len(resources) == 1
    assert resources[0].path == PurePosixPath("folderA/subfolderA/file.txt")


def test_save_same_resource_twice(dao: StudyDao) -> None:
    dao.save_user_resources(
        [
            UserResourceDataCreation(path=PurePosixPath("folderB/subfolderB"), resource_type=ResourceType.FOLDER),
            UserResourceDataCreation(path=PurePosixPath("folderB/subfolderB"), resource_type=ResourceType.FOLDER),
        ]
    )
    resources = dao.get_all_user_resources()
    assert len(resources) == 1
    assert resources[0].path == PurePosixPath("folderB/subfolderB")

    # Specific DB test. Ensure we only have 2 entries in DB: `folderB` and `subfolderB`
    if isinstance(dao, DatabaseStudyDao):
        assert len(dao.get_session().execute(select(USER_RESOURCES_TABLE)).all()) == 2


def test_save_folder_inside_an_existing_one(dao: StudyDao) -> None:
    dao.save_user_resources([UserResourceDataCreation(path=PurePosixPath("a"), resource_type=ResourceType.FOLDER)])
    dao.save_user_resources([UserResourceDataCreation(path=PurePosixPath("a/b"), resource_type=ResourceType.FOLDER)])

    resources = dao.get_all_user_resources()
    assert len(resources) == 1
    assert resources[0].path == PurePosixPath("a/b")

    dao.save_user_resources(
        [
            UserResourceDataCreation(path=PurePosixPath("c"), resource_type=ResourceType.FOLDER),
            UserResourceDataCreation(path=PurePosixPath("c/d"), resource_type=ResourceType.FOLDER),
        ]
    )

    resources = dao.get_all_user_resources()
    assert len(resources) == 2


def test_save_a_file_with_the_same_name_as_an_existing_folder(dao: StudyDao, blob_service: InMemoryBlobService) -> None:
    blob_id = blob_service.save(b"content")

    if isinstance(dao, DatabaseStudyDao):
        expected_error = ValueError
        expected_msg = "Cannot create 2 resources of different type at the same path"
    else:
        expected_error = IsADirectoryError
        expected_msg = "user/a"

    with pytest.raises(expected_error, match=expected_msg):
        dao.save_user_resources(
            [
                UserResourceDataCreation(path=PurePosixPath("a"), resource_type=ResourceType.FOLDER),
                UserResourceDataCreation(path=PurePosixPath("a"), resource_type=ResourceType.FILE, blob_id=blob_id),
            ]
        )
