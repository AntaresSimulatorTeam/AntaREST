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

from typing import Optional

from antarest.core.application import AppBuildContext
from antarest.core.config import Config
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.filetransfer.web import create_file_transfer_api
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.service import ITaskService


def build_filetransfer_service(
    app_ctxt: Optional[AppBuildContext], event_bus: IEventBus, task_service: ITaskService, config: Config
) -> FileTransferManager:
    ftm = FileTransferManager(
        repository=FileDownloadRepository(), event_bus=event_bus, task_service=task_service, config=config
    )

    if app_ctxt:
        app_ctxt.api_root.include_router(create_file_transfer_api(ftm, config))
    return ftm
