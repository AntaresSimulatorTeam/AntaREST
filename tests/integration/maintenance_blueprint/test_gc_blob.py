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

"""Integration tests for the blob garbage collection task."""

import uuid

from antarest.blobstore.service import BlobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, GarbageCollectorTaskResult, LockId
from antarest.maintenance.tasks.gc_blob import clean_blobs
from antarest.study.business.model.user_model import ResourceType
from antarest.study.dao.database.database_blob_usage_provider import DatabaseBlobUsageProvider
from antarest.study.dao.database.models import STUDY_DATA_CONTAINER_TABLE
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE
from tests.helpers import create_study


class TestCleanBlobsIntegration:
    def test_deletes_unused_blobs(self, simple_blob_service: BlobService):
        blob_id = simple_blob_service.save(b"Test content")
        assert blob_id in simple_blob_service.get_saved_blobs()

        with db():
            result = clean_blobs(
                blob_service=simple_blob_service,
                dry_run=False,
            )

        assert isinstance(result, GarbageCollectorTaskResult)
        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is False

        assert blob_id not in simple_blob_service.get_saved_blobs()

    def test_dry_run_does_not_delete(self, simple_blob_service: BlobService):
        blob_id = simple_blob_service.save(b"Test content for dry run")
        assert blob_id in simple_blob_service.get_saved_blobs()

        with db():
            result = clean_blobs(
                blob_service=simple_blob_service,
                dry_run=True,
            )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        assert result.dry_run is True

        # Blob should still exist because dry_run is True
        assert blob_id in simple_blob_service.get_saved_blobs()

    def test_returns_success_with_no_blobs(self, simple_blob_service: BlobService):
        with db():
            result = clean_blobs(
                blob_service=simple_blob_service,
                dry_run=False,
            )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 0
        assert result.duration_seconds >= 0

    def test_deletes_multiple_unused_blobs(self, simple_blob_service: BlobService):
        blob_ids = [
            simple_blob_service.save(b"Content 1"),
            simple_blob_service.save(b"Content 2"),
            simple_blob_service.save(b"Content 3"),
        ]

        for blob_id in blob_ids:
            assert blob_id in simple_blob_service.get_saved_blobs()

        with db():
            result = clean_blobs(
                blob_service=simple_blob_service,
                dry_run=False,
            )

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 3

        for blob_id in blob_ids:
            assert blob_id not in simple_blob_service.get_saved_blobs()

    def test_returns_skipped_when_lock_held(self, simple_blob_service: BlobService):
        with db():
            with create_lock(db.session, lock_id=LockId.BLOB_GC):
                result = clean_blobs(blob_service=simple_blob_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SKIPPED
        assert result.reason == "lock_not_acquired"

    def test_does_not_delete_blobs_used_by_user_resources(self, simple_blob_service: BlobService):
        # Save two blobs: one referenced by a user resource, one not
        used_blob_id = simple_blob_service.save(b"Used by user resource")
        unused_blob_id = simple_blob_service.save(b"Orphan blob")

        # Register the provider so the GC knows about user resources
        simple_blob_service.register_usage_provider(DatabaseBlobUsageProvider())

        # Insert a study and a user resource referencing the blob
        study_id = str(uuid.uuid4())
        with db():
            db.session.add(create_study(id=study_id, name="Test Study", version="880"))
            db.session.flush()
            db.session.execute(STUDY_DATA_CONTAINER_TABLE.insert().values(study_id=study_id))
            db.session.execute(
                USER_RESOURCES_TABLE.insert().values(
                    study_id=study_id,
                    path="my_file.txt",
                    resource_type=ResourceType.FILE,
                    blob_id=used_blob_id,
                )
            )
            db.session.commit()

        # Run GC
        with db():
            result = clean_blobs(blob_service=simple_blob_service, dry_run=False)

        assert result.status == BackGroundTaskStatus.SUCCESS
        assert result.deleted_count == 1
        # The used blob should still exist
        assert used_blob_id in simple_blob_service.get_saved_blobs()
        # The orphan blob should be deleted
        assert unused_blob_id not in simple_blob_service.get_saved_blobs()
