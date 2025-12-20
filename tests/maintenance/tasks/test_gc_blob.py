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

"""Tests for blob GC task."""

from unittest.mock import Mock

import pytest

from antarest.maintenance.app import celery_app
from antarest.maintenance.tasks.gc_blob import _delete_blobs
from antarest.maintenance.tasks.gc_blob_task import clean_blobs_task


class TestDeleteBlobs:
    def test_deletes_blobs_when_not_dry_run(self):
        mock_service = Mock()
        _delete_blobs(mock_service, {"blob1", "blob2", "blob3"}, dry_run=False)

        assert mock_service.delete.call_count == 3
        mock_service.delete.assert_any_call("blob1")
        mock_service.delete.assert_any_call("blob2")
        mock_service.delete.assert_any_call("blob3")

    def test_does_not_delete_when_dry_run(self):
        mock_service = Mock()
        _delete_blobs(mock_service, {"blob1", "blob2"}, dry_run=True)
        mock_service.delete.assert_not_called()

    def test_empty_set(self):
        mock_service = Mock()
        _delete_blobs(mock_service, set(), dry_run=False)
        mock_service.delete.assert_not_called()

    def test_returns_failure_count(self):
        mock_service = Mock()
        mock_service.delete.side_effect = [None, Exception("fail"), None]
        failures = _delete_blobs(mock_service, {"b1", "b2", "b3"}, dry_run=False)
        assert failures == 1


class TestCleanBlobsTask:
    def test_raises_without_context(self, celery_ctx_backup):
        celery_app.conf.maintenance_ctx = None
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            clean_blobs_task.run()
