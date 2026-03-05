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

"""Task action handlers for watcher operations."""

from __future__ import annotations

import logging
from typing import Optional

from antarest.core.tasks.action import TaskActionParams, TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


class WatcherScanParams(TaskActionParams):
    recursive: bool = True
    workspace: Optional[str] = None
    path: Optional[str] = None


@TaskActionRegistry.register("watcher_scan", WatcherScanParams)
def handle_watcher_scan(services: CoreServices, params: WatcherScanParams, notifier: ITaskNotifier) -> TaskResult:
    """Execute a watcher scan.

    Note: This handler needs the Watcher instance which is not part of CoreServices.
    The scan logic is delegated to StudyService since Watcher is created separately.
    For the in-process TaskJobService path, the Watcher is available.
    For the Celery path, a fresh scan is created from config + study_service.
    """
    from antarest.study.storage.rawstudy.watcher import Watcher

    config = services.study_service.storage_service.raw_study_service.config

    watcher = Watcher(
        config=config,
        study_service=services.study_service,
        task_service=services.task_service,
    )
    watcher.scan(params.recursive, params.workspace, params.path)
    return TaskResult(success=True, message="Scan completed")
