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

from antarest.core.config import Config
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import IEventBus


def build_filetransfer_service(event_bus: IEventBus, config: Config) -> FileTransferManager:
    return FileTransferManager(repository=FileDownloadRepository(), event_bus=event_bus, config=config)
