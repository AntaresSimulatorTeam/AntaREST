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

import logging
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.pool import NullPool

from antarest.core.config import Config, RedisConfig
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.metrics import add_db_metrics
from antarest.core.persistence import upgrade_db
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.worker import AbstractWorker

logger = logging.getLogger(__name__)


SESSION_ARGS: dict[str, bool] = {
    "autocommit": False,
    "expire_on_commit": False,
    "autoflush": False,
}
"""
This mapping can be used to instantiate a new session, for example:

>>> with sessionmaker(engine, **SESSION_ARGS)() as session:
...     session.execute("SELECT 1")
"""


class Module(StrEnum):
    APP = "app"
    WATCHER = "watcher"
    MATRIX_GC = "matrix_gc"
    ARCHIVE_WORKER = "archive_worker"
    AUTO_ARCHIVER = "auto_archiver"
    BLOB_GC = "blob_gc"
    VARIABLE_VIEW_GC = "variable_view_gc"


def init_db_engine(
    config: Config,
    auto_upgrade_db: bool,
    config_file: Path | None = None,
) -> Engine:
    if auto_upgrade_db:
        if not config_file:
            raise ValueError("config_file must be provided when auto_upgrade_db is True")
        upgrade_db(config_file)
    connect_args: Dict[str, Any] = {}
    if config.db.db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    else:
        connect_args["connect_timeout"] = config.db.db_connect_timeout

    extra: dict[str, Any] = {}
    if config.db.pool_use_null:
        extra["poolclass"] = NullPool
    elif not config.db.db_url.startswith("sqlite"):
        if config.db.pool_pre_ping:
            extra["pool_pre_ping"] = True
        if config.db.pool_recycle:
            extra["pool_recycle"] = config.db.pool_recycle
        if config.db.pool_max_overflow:
            extra["max_overflow"] = config.db.pool_max_overflow
        if config.db.pool_size:
            extra["pool_size"] = config.db.pool_size
        if config.db.pool_use_lifo:
            extra["pool_use_lifo"] = config.db.pool_use_lifo

    engine = create_engine(config.db.db_url, echo=config.debug, connect_args=connect_args, **extra)

    add_db_metrics(config)

    return engine


def new_redis_instance(config: RedisConfig) -> redis.Redis:  # type: ignore
    redis_client = redis.Redis(
        host=config.host,
        port=config.port,
        password=config.password,
        db=0,
        retry_on_error=[redis.ConnectionError, redis.TimeoutError],
    )
    return redis_client


def create_archive_worker(
    config: Config,
    workspace: str,
    local_root: Path = Path("/"),
    event_bus: Optional[IEventBus] = None,
) -> AbstractWorker:
    if not event_bus:
        import asyncio

        from antarest.dishka_provider import make_container

        container = make_container(config)
        event_bus = asyncio.run(container.get(IEventBus))
    return ArchiveWorker(event_bus, workspace, local_root, config)
