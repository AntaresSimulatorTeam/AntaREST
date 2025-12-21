# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.blobstore.service import BlobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.maintenance.tasks.common import GCTaskResult, LockId, TaskStatus
from antarest.maintenance.tasks.gc_blob import clean_blobs


class TestCleanBlobsIntegration:
    def test_deletes_unused_blobs(self, simple_blob_service: BlobService):
        blob_id = simple_blob_service.save(b"Test content")
        assert blob_id in simple_blob_service.get_saved_blobs()

        with db():
            result = clean_blobs(
                blob_service=simple_blob_service,
                dry_run=False,
            )

        assert isinstance(result, GCTaskResult)
        assert result.status == TaskStatus.SUCCESS
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

        assert result.status == TaskStatus.SUCCESS
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

        assert result.status == TaskStatus.SUCCESS
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

        assert result.status == TaskStatus.SUCCESS
        assert result.deleted_count == 3

        for blob_id in blob_ids:
            assert blob_id not in simple_blob_service.get_saved_blobs()

    def test_returns_skipped_when_lock_held(self, simple_blob_service: BlobService):
        with db():
            with create_lock(db.session, lock_id=LockId.BLOB_GC):
                result = clean_blobs(blob_service=simple_blob_service, dry_run=False)

        assert result.status == TaskStatus.SKIPPED
        assert result.reason == "lock_not_acquired"
