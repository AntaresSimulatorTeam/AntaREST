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

import time
from pathlib import Path
from typing import Dict, List, cast

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.core.utils.utils import get_local_path
from antarest.service_creator import (
    SESSION_ARGS,
    Module,
    create_archive_worker,
    create_core_services,
    create_matrix_gc,
    create_watcher,
    init_db_engine,
)
from antarest.study.storage.auto_archive_service import AutoArchiveService


def _init(config_file: Path, services_list: List[Module]) -> Dict[Module, IService]:
    res = get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    engine = init_db_engine(
        config_file,
        config,
        False,
    )
    DBSessionMiddleware(None, custom_engine=engine, session_args=cast(Dict[str, bool], SESSION_ARGS))
    configure_logger(config)

    core_services = create_core_services(None, config)

    services: Dict[Module, IService] = {}

    if Module.WATCHER in services_list:
        watcher = create_watcher(config=config, app_ctxt=None, study_service=core_services.study_service)
        services[Module.WATCHER] = watcher

    if Module.MATRIX_GC in services_list:
        matrix_gc = create_matrix_gc(
            config=config,
            app_ctxt=None,
            study_service=core_services.study_service,
            matrix_service=core_services.matrix_service,
        )
        services[Module.MATRIX_GC] = matrix_gc

    if Module.ARCHIVE_WORKER in services_list:
        worker = create_archive_worker(config, "test", event_bus=core_services.event_bus)
        services[Module.ARCHIVE_WORKER] = worker

    if Module.AUTO_ARCHIVER in services_list:
        auto_archive_service = AutoArchiveService(core_services.study_service, core_services.output_service, config)
        services[Module.AUTO_ARCHIVER] = auto_archive_service

    return services


def start_all_services(config_file: Path, services_list: List[Module]) -> None:
    """
    Start all services in a worker.

    This function is used to start all services in a worker.
    Each worker is started in a different docker image.

    Args:
        config_file: Path to the configuration file (`application.yaml`)
        services_list: List of services to start.
    """
    services = _init(config_file, services_list)
    for service in services:
        services[service].start(threaded=True)
    # Once started, the worker must wait indefinitely (demon service).
    # This loop may be interrupted using Crl+C
    while True:
        time.sleep(2)
