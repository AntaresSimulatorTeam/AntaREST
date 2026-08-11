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

from sqlalchemy.orm import Session

from antarest.blobstore.model import BlobReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.database.database_blob_usage_provider import DatabaseBlobUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_8_8
from tests.conftest import build_db_dao


def test_blob_usage_provider_returns_blob_ids(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resources(
        [
            UserResourceDataCreation(
                path=PurePosixPath("file1.txt"), resource_type=ResourceType.FILE, blob_id="blob_aaa"
            ),
            UserResourceDataCreation(
                path=PurePosixPath("file2.txt"), resource_type=ResourceType.FILE, blob_id="blob_bbb"
            ),
        ]
    )

    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert len(used_blobs) == 2
    blob_ids = {b.blob_id for b in used_blobs}
    assert blob_ids == {"blob_aaa", "blob_bbb"}
    assert all(isinstance(b, BlobReference) for b in used_blobs)


def test_blob_usage_provider_ignores_folders(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_user_resources(
        [
            UserResourceDataCreation(
                path=PurePosixPath("file.txt"), resource_type=ResourceType.FILE, blob_id="blob_aaa"
            ),
            UserResourceDataCreation(path=PurePosixPath("my_folder"), resource_type=ResourceType.FOLDER),
        ]
    )

    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert len(used_blobs) == 1
    assert used_blobs[0].blob_id == "blob_aaa"


def test_blob_usage_provider_reports_every_study(
    db_dao: DatabaseStudyDao, db_session: Session, matrix_service: ISimpleMatrixService
) -> None:
    """
    The provider walks all studies at once. Since `user_resources` is keyed by `study_data_id`,
    the study each blob is used by is recovered by a join, which must not lose or mix up rows.
    """
    other_dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    db_dao.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("a.txt"), resource_type=ResourceType.FILE, blob_id="blob_aaa")]
    )
    other_dao.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("b.txt"), resource_type=ResourceType.FILE, blob_id="blob_bbb")]
    )

    provider = DatabaseBlobUsageProvider()
    usage = {b.blob_id: b.use_description for b in provider.get_blob_usage()}

    assert usage == {
        "blob_aaa": f"Used by study {db_dao.get_study_id()}",
        "blob_bbb": f"Used by study {other_dao.get_study_id()}",
    }


def test_blob_usage_provider_empty() -> None:
    provider = DatabaseBlobUsageProvider()
    used_blobs = list(provider.get_blob_usage())

    assert used_blobs == []
