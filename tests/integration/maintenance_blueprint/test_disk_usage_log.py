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

"""Integration tests for the disk usage log."""

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import create_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId
from antarest.maintenance.tasks.disk_usage_log import disk_usage_logging


class TestDiskUsageLogIntegration:
    def test_disk_usage_log(self):
        with db():
            result = disk_usage_logging(Config(), False)
        assert result.status == BackGroundTaskStatus.SUCCESS

    def test_returns_skipped_when_lock_held(self):
        with db():
            with create_lock(db.session, lock_id=LockId.DISK_USAGE):
                result = disk_usage_logging(Config(), False)

            assert result.status == BackGroundTaskStatus.SKIPPED
