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

"""Disk usage logging task."""

import logging
import shutil
import time

from antarest.core.maintenance.service import MaintenanceService

logger = logging.getLogger(__name__)


class DiskUsageTaskResult:
    pass #TODO:

def check_disk_usage(self) -> None:
    while True:
        for name, workspace in self.config.storage.workspaces.items():
            try:
                usage = shutil.disk_usage(workspace.path)
                logger.info(
                    f"Disk usage for {name}: {(100 * usage.used / usage.total):.2f}%"
                    f" ({(usage.free / 1000000000):.3f}GB free)"
                )

                if self._metrics:
                    self._metrics.update_disk_usage(name, free=usage.free, used=usage.used, total=usage.total)

            except Exception as e:
                logger.error(
                    f"Failed to check disk usage for disk {workspace.path}",
                    exc_info=e,
                )
        time.sleep(3600)


def disk_usage_logging():
    pass
