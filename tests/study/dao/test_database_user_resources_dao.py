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

from antarest.core.exceptions import UserResourcesNotFound
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_save_user_resources_file(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resource(
        UserResourceDataCreation(
            path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id="test_blob_id"
        )
    )

    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].path == PurePosixPath("file_path")
    assert result[0].resource_type == ResourceType.FILE
    assert result[0].blob_id == "test_blob_id"

    dao.delete_user_resource(PurePosixPath("file_path"))

    assert len(list(dao.get_all_user_resources())) == 0


def test_save_user_resources_folder(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resource(
        UserResourceDataCreation(path=PurePosixPath("folder_path"), resource_type=ResourceType.FOLDER)
    )
    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].path == PurePosixPath("folder_path")
    assert result[0].resource_type == ResourceType.FOLDER
    assert result[0].blob_id is None


def test_update_blob_id(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    resource = UserResourceDataCreation(
        path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id="test_blob_id"
    )
    dao.save_user_resource(resource)

    updated_resource = UserResourceDataCreation(
        path=PurePosixPath("file_path"), resource_type=ResourceType.FILE, blob_id="test_blob_id_updated"
    )
    dao.save_user_resource(updated_resource)

    result = list(dao.get_all_user_resources())
    assert len(result) == 1
    assert result[0].blob_id == "test_blob_id_updated"


def test_user_resources_not_exists(db_dao: DatabaseStudyDao) -> None:
    with pytest.raises(UserResourcesNotFound):
        db_dao.delete_user_resource(PurePosixPath("file_path"))
