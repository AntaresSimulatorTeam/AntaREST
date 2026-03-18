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

import asyncio
import time
from pathlib import Path
from typing import List

from antarest.blobstore.blob_garbage_collector import BlobGarbageCollector
from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.interfaces.service import IService
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.core.utils.utils import get_local_path
from antarest.dishka_provider import make_container
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.service_creator import (
    SESSION_ARGS,
    Module,
    create_archive_worker,
    init_db_engine,
)
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.rawstudy.watcher import Watcher


def _init(config_file: Path, services_list: List[Module]) -> list[IService]:
    res = get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_file)
    engine = init_db_engine(config, False, config_file)
    init_db_singleton(custom_engine=engine, session_args=SESSION_ARGS)
    configure_logger(config)

    container = make_container(config)

    async def _get(t: type):
        return await container.get(t)

    def get(t: type):
        return asyncio.run(_get(t))

    services: list[IService] = []

    if Module.WATCHER in services_list:
        services.append(get(Watcher))

    if Module.MATRIX_GC in services_list:
        services.append(get(MatrixGarbageCollector))

    if Module.BLOB_GC in services_list:
        services.append(get(BlobGarbageCollector))

    if Module.AUTO_ARCHIVER in services_list:
        services.append(get(AutoArchiveService))

    if Module.ARCHIVE_WORKER in services_list:
        event_bus = get(IEventBus)
        worker = create_archive_worker(config, "test", event_bus=event_bus)
        services.append(worker)

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
        service.start(threaded=True)
    # Once started, the worker must wait indefinitely (demon service).
    # This loop may be interrupted using Crl+C
    while True:
        time.sleep(2)
