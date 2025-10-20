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

import logging
import os
import time
from typing import Any

import prometheus_client
from fastapi import FastAPI
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    make_asgi_app,
    multiprocess,
)
from sqlalchemy import Engine, Pool, PoolProxiedConnection
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session, SessionTransaction, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry
from starlette.requests import Request
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import ConfigurationError
from antarest.core.tasks.service import TaskServiceListener

logger = logging.getLogger(__name__)


_PROMETHEUS_MULTIPROCESS_ENV_VAR = "PROMETHEUS_MULTIPROC_DIR"

WORKER_ID = str(os.getpid())


def _add_db_metrics(registry: CollectorRegistry = prometheus_client.REGISTRY) -> None:
    """
    Registers metrics related to database activity.
    """
    _add_db_connection_metrics(registry)
    _add_db_session_metrics(registry)


def _add_db_connection_metrics(registry: CollectorRegistry, engine: Engine | None = None) -> None:
    """
    Register connection-level (low level) DB metrics
    """
    target = engine or Pool

    dbconn_durations_histo = Histogram(
        "dbconn_duration_seconds",
        "DB connection duration",
        ["worker_id"],
        registry=registry,
    )

    dbconn_gauge = Gauge(
        "dbconn_in_use",
        "DB connection count",
        ["worker_id"],
        multiprocess_mode="liveall",
        registry=registry,
    )
    dbconn_gauge.labels(WORKER_ID).set(0)

    checkout_counter = Counter(
        "dbconn_checkout_count",
        "DB connection checkouts",
        ["worker_id"],
        registry=registry,
    )

    checkin_counter = Counter(
        "dbconn_checkin_count",
        "DB connection checkins",
        ["worker_id"],
        registry=registry,
    )

    dbconn_gauge.labels(WORKER_ID).set(0)

    @listens_for(target, "checkin")
    def on_checkin(dbapi_con: Any, connection_record: ConnectionPoolEntry) -> None:
        checkin_counter.labels(WORKER_ID).inc()
        try:
            start_time = connection_record.info["start_time"]
        except KeyError:
            return
        dbconn_gauge.labels(WORKER_ID).dec()

        dbconn_durations_histo.labels(WORKER_ID).observe(time.time() - start_time)

    @listens_for(target, "checkout")
    def on_checkout(
        dbapi_con: Any, connection_record: ConnectionPoolEntry, connection_proxy: PoolProxiedConnection
    ) -> None:
        checkout_counter.labels(WORKER_ID).inc()
        dbconn_gauge.labels(WORKER_ID).inc()

        connection_record.info["start_time"] = time.time()


def _add_db_session_metrics(registry: CollectorRegistry, session_factory: sessionmaker[Session] | None = None) -> None:
    """
    Register ORM-level DB metrics:
     -
    """
    target = session_factory or Session

    transactions_current_gauge = Gauge(
        "transaction_current",
        "Transaction in progress",
        ["worker_id"],
        multiprocess_mode="liveall",
        registry=registry,
    )
    transactions_current_gauge.labels(WORKER_ID).set(0)

    transaction_duration_histo = Histogram(
        "transaction_duration_seconds",
        "Transaction ends",
        ["worker_id"],
        registry=registry,
    )

    events_counter = Counter(
        "dbsession_events",
        "Begins counter",
        ["worker_id", "event_type"],
        registry=registry,
    )

    @listens_for(target, "after_begin")
    def after_begin(session: Session, connection: Any, transaction: Any) -> None:
        events_counter.labels(WORKER_ID, "begin").inc()

    @listens_for(target, "after_commit")
    def after_commit(session: Session) -> None:
        events_counter.labels(WORKER_ID, "commit").inc()

    @listens_for(target, "after_rollback")
    def after_rollback(session: Session) -> None:
        events_counter.labels(WORKER_ID, "rollback").inc()

    @listens_for(target, "after_transaction_create")
    def after_transaction_create(session: Session, transaction: SessionTransaction) -> None:
        transactions_current_gauge.labels(WORKER_ID).inc()
        session.info["start_time"] = time.time()

    @listens_for(target, "after_transaction_end")
    def after_transaction_end(session: Session, transaction: SessionTransaction) -> None:
        transactions_current_gauge.labels(WORKER_ID).dec()
        if "start_time" in session.info:
            transaction_duration_histo.labels(WORKER_ID).observe(time.time() - session.info["start_time"])
            del session.info["start_time"]


def _add_metrics_middleware(application: FastAPI) -> None:
    """
    Registers an HTTP middleware to report metrics about requests count and duration
    """

    request_counter = Counter(
        "request_count",
        "App Request Count",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=prometheus_client.REGISTRY,
    )
    request_duration_histo = Histogram(
        "request_duration_seconds",
        "Request duration",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=prometheus_client.REGISTRY,
    )

    @application.middleware("http")
    async def add_metrics(request: Request, call_next: Any) -> Any:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        if "route" in request.scope:
            request_path = request.scope["root_path"] + request.scope["route"].path
        else:
            request_path = request.url.path

        request_counter.labels(WORKER_ID, request.method, request_path, response.status_code).inc()
        request_duration_histo.labels(WORKER_ID, request.method, request_path, response.status_code).observe(
            process_time
        )
        return response


def add_metrics(application: FastAPI, config: Config) -> None:
    """
    If configured, adds "/metrics" endpoint to report metrics to prometheus.
    Also registers metrics for HTTP requests.
    """
    prometheus_config = config.metrics.prometheus
    if not prometheus_config:
        return

    prometheus_client.disable_created_metrics()  # type: ignore

    if prometheus_config.multiprocess:
        if _PROMETHEUS_MULTIPROCESS_ENV_VAR not in os.environ:
            raise ConfigurationError(
                f"Environment variable {_PROMETHEUS_MULTIPROCESS_ENV_VAR} must be defined for use of prometheus in a multiprocess environment"
            )
        global_registry = CollectorRegistry(auto_describe=True)
        multiprocess.MultiProcessCollector(global_registry)  # type: ignore
    else:
        global_registry = prometheus_client.REGISTRY

    metrics_app = make_asgi_app(registry=global_registry)
    application.mount("/metrics", metrics_app)

    _add_metrics_middleware(application)
    _add_db_metrics()


class TasksMetricsRecorder(TaskServiceListener):
    """
    Exports metrics for tasks: wait time before execution, duration, ...
    """

    def __init__(self, registry: CollectorRegistry) -> None:
        self._duration_histo = Histogram(
            "tasks_duration_seconds",
            "Tasks duration in seconds",
            ["worker_id"],
            registry=registry,
        )
        self._wait_time_histo = Histogram(
            "tasks_wait_seconds",
            "Tasks duration in seconds",
            ["worker_id"],
            registry=registry,
        )
        self._running_gauge = Gauge(
            "tasks_running",
            "Count of running tasks",
            ["worker_id"],
            multiprocess_mode="liveall",
            registry=registry,
        )
        self._pending_gauge = Gauge(
            "tasks_pending",
            "Count of pending tasks",
            ["worker_id"],
            multiprocess_mode="liveall",
            registry=registry,
        )

        self._submit_times: dict[str, float] = {}
        self._start_times: dict[str, float] = {}

    @override
    def on_task_submit(self, task_id: str) -> None:
        self._pending_gauge.labels(WORKER_ID).inc()
        self._submit_times[task_id] = time.time()

    @override
    def on_task_start(self, task_id: str) -> None:
        self._pending_gauge.labels(WORKER_ID).dec()
        self._running_gauge.labels(WORKER_ID).inc()
        self._wait_time_histo.labels(WORKER_ID).observe(time.time() - self._submit_times[task_id])
        del self._submit_times[task_id]
        self._start_times[task_id] = time.time()

    @override
    def on_task_end(self, task_id: str) -> None:
        self._running_gauge.labels(WORKER_ID).dec()
        self._duration_histo.labels(WORKER_ID).observe(time.time() - self._start_times[task_id])
        del self._start_times[task_id]
