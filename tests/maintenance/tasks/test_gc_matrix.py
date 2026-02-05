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

"""Tests for matrix GC task."""

from unittest.mock import Mock

import pytest

from antarest.maintenance.tasks.gc_matrix import _delete_matrices
from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task


class TestDeleteMatrices:
    def test_deletes_matrices_when_not_dry_run(self):
        mock_service = Mock()
        _delete_matrices(mock_service, {"m1", "m2", "m3"}, dry_run=False)

        assert mock_service.delete.call_count == 3
        mock_service.delete.assert_any_call("m1")
        mock_service.delete.assert_any_call("m2")
        mock_service.delete.assert_any_call("m3")

    def test_does_not_delete_when_dry_run(self):
        mock_service = Mock()
        _delete_matrices(mock_service, {"m1", "m2"}, dry_run=True)
        mock_service.delete.assert_not_called()

    def test_empty_set(self):
        mock_service = Mock()
        _delete_matrices(mock_service, set(), dry_run=False)
        mock_service.delete.assert_not_called()

    def test_returns_failure_count(self):
        mock_service = Mock()
        mock_service.delete.side_effect = [None, Exception("fail"), None]
        failures = _delete_matrices(mock_service, {"m1", "m2", "m3"}, dry_run=False)
        assert failures == 1


class TestCleanMatricesTask:
    def test_raises_without_context(self, with_no_maintenance_ctx):
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            clean_matrices_task.run()
