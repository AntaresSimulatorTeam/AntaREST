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

from antarest.blobstore.model import BlobReference
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.database.database_blob_usage_provider import DatabaseBlobUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_blob_usage_provider_returns_blob_ids(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resource(
        UserResourceDataCreation(path=PurePosixPath("file1.txt"), resource_type=ResourceType.FILE, blob_id="blob_aaa")
    )
    dao.save_user_resource(
        UserResourceDataCreation(path=PurePosixPath("file2.txt"), resource_type=ResourceType.FILE, blob_id="blob_bbb")
    )

    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert len(used_blobs) == 2
    blob_ids = {b.blob_id for b in used_blobs}
    assert blob_ids == {"blob_aaa", "blob_bbb"}
    assert all(isinstance(b, BlobReference) for b in used_blobs)


def test_blob_usage_provider_ignores_folders(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resource(
        UserResourceDataCreation(path=PurePosixPath("file.txt"), resource_type=ResourceType.FILE, blob_id="blob_aaa")
    )
    dao.save_user_resource(UserResourceDataCreation(path=PurePosixPath("my_folder"), resource_type=ResourceType.FOLDER))

    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert len(used_blobs) == 1
    assert used_blobs[0].blob_id == "blob_aaa"


def test_blob_usage_provider_empty() -> None:
    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert used_blobs == []
