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

"""Task action handlers for launcher operations."""

from __future__ import annotations

import logging
from pathlib import Path

from antarest.core.tasks.action import TaskActionParams, TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


class ExportLauncherResultParams(TaskActionParams):
    output_path: str
    export_path: str
    export_id: str


@TaskActionRegistry.register("export_launcher_result", ExportLauncherResultParams)
def handle_export_launcher_result(
    services: CoreServices, params: ExportLauncherResultParams, notifier: ITaskNotifier
) -> TaskResult:
    output_path = Path(params.output_path)
    export_path = Path(params.export_path)

    try:
        archive_dir(output_path, export_path, archive_format=ArchiveFormat.ZIP)
        services.file_transfer_manager.set_ready(params.export_id)
        return TaskResult(success=True, message="")
    except Exception as e:
        services.file_transfer_manager.fail(params.export_id, str(e))
        raise e
