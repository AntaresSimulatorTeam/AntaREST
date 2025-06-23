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
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.tasks.service import ITaskService
from antarest.launcher.repository import JobResultRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.login.service import LoginService
from antarest.study.service import StudyService
from antarest.study.storage.output_service import OutputService


def build_launcher(
    app_ctxt: Optional[AppBuildContext],
    config: Config,
    study_service: StudyService,
    output_service: OutputService,
    login_service: LoginService,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    cache: ICache,
    event_bus: IEventBus = DummyEventBusService(),
    service_launcher: Optional[LauncherService] = None,
) -> Optional[LauncherService]:
    if not service_launcher:
        repository = JobResultRepository()
        # keep old job results
        #        study_service.add_on_deletion_callback(repository.delete_by_study_id)
        service_launcher = LauncherService(
            config=config,
            study_service=study_service,
            output_service=output_service,
            login_service=login_service,
            job_result_repository=repository,
            event_bus=event_bus,
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
            cache=cache,
        )

    if service_launcher and app_ctxt:
        app_ctxt.api_root.include_router(create_launcher_api(service_launcher, config))

    return service_launcher
