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

"""Tests for the disk usage log task."""

import pytest

from antarest.maintenance.tasks.disk_usage_log_task import disk_usage_log_task


class TestDiskUsageLogTask:
    def test_raises_without_context(self, with_no_maintenance_ctx):
        with pytest.raises(RuntimeError, match="MaintenanceContext not in app.conf"):
            disk_usage_log_task.run()
