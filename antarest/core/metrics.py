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
import os
import time
from http import HTTPStatus
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
from sqlalchemy.orm import ORMExecuteState, Session, SessionTransaction, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry
from starlette.requests import Request
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import ConfigurationError
from antarest.core.tasks.model import TaskStatus, TaskType
from antarest.core.tasks.service import TaskServiceListener
from antarest.globals import ANTAREST_WORKER_ID

logger = logging.getLogger(__name__)


_PROMETHEUS_MULTIPROCESS_ENV_VAR = "PROMETHEUS_MULTIPROC_DIR"

WORKER_ID = str(ANTAREST_WORKER_ID)


def add_db_metrics(config: Config) -> None:
    """
    Registers metrics related to database activity.
    """
    if config.metrics.prometheus:
        _add_db_metrics(prometheus_client.REGISTRY)


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
        "db_connections_duration_seconds",
        "DB connection duration",
        ["worker_id"],
        registry=registry,
    )

    dbconn_gauge = Gauge(
        "db_connections_used",
        "DB connection count",
        ["worker_id"],
        multiprocess_mode="liveall",
        registry=registry,
    )
    dbconn_gauge.labels(WORKER_ID).set(0)

    dbconn_idle_gauge = Gauge(
        "db_connections_idle",
        "Idle DB connection count",
        ["worker_id"],
        multiprocess_mode="liveall",
        registry=registry,
    )
    dbconn_idle_gauge.labels(WORKER_ID).set(0)

    dbconn_event_counter = Counter(
        "db_connections_events",
        "DB connection events",
        ["worker_id", "event_type"],
        registry=registry,
    )

    @listens_for(target, "connect")
    def on_connect(dbapi_con: Any, connection_record: ConnectionPoolEntry) -> None:
        dbconn_idle_gauge.labels(WORKER_ID).inc()
        dbconn_event_counter.labels(WORKER_ID, "connect").inc()

    @listens_for(target, "close")
    def on_close(dbapi_con: Any, connection_record: ConnectionPoolEntry) -> None:
        dbconn_idle_gauge.labels(WORKER_ID).dec()
        dbconn_event_counter.labels(WORKER_ID, "close").inc()

    @listens_for(target, "detach")
    def on_detach(dbapi_con: Any, connection_record: ConnectionPoolEntry) -> None:
        dbconn_gauge.labels(WORKER_ID).dec()
        dbconn_event_counter.labels(WORKER_ID, "detach").inc()

    @listens_for(target, "invalidate")
    def on_invalidate(dbapi_con: Any, connection_record: ConnectionPoolEntry, exception: Any) -> None:
        dbconn_event_counter.labels(WORKER_ID, "invalidate").inc()
        # close will be called, no need to decrement idle gauge

    @listens_for(target, "checkin")
    def on_checkin(dbapi_con: Any, connection_record: ConnectionPoolEntry) -> None:
        dbconn_event_counter.labels(WORKER_ID, "checkin").inc()
        dbconn_idle_gauge.labels(WORKER_ID).inc()
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
        dbconn_event_counter.labels(WORKER_ID, "checkout").inc()
        dbconn_idle_gauge.labels(WORKER_ID).dec()
        dbconn_gauge.labels(WORKER_ID).inc()

        connection_record.info["start_time"] = time.time()


def _add_db_session_metrics(registry: CollectorRegistry, session_factory: sessionmaker[Session] | None = None) -> None:
    """
    Register ORM-level DB metrics:
    """
    target = session_factory or Session

    transactions_current_gauge = Gauge(
        "db_transactions_current",
        "Transaction in progress",
        ["worker_id"],
        multiprocess_mode="liveall",
        registry=registry,
    )
    transactions_current_gauge.labels(WORKER_ID).set(0)

    transaction_duration_histo = Histogram(
        "db_transactions_duration_seconds",
        "Transaction ends",
        ["worker_id"],
        registry=registry,
    )

    events_counter = Counter(
        "db_session_events",
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

    @listens_for(target, "do_orm_execute")
    def on_select(orm_execute_state: ORMExecuteState) -> None:
        if orm_execute_state.is_select:
            events_counter.labels(WORKER_ID, "select").inc()


def _add_metrics_middleware(registry: CollectorRegistry, application: FastAPI) -> None:
    """
    Registers an HTTP middleware to report metrics about requests count and duration
    """

    request_counter = Counter(
        "http_requests",
        "HTTP requests count",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=registry,
    )
    request_duration_histo = Histogram(
        "http_requests_duration_seconds",
        "HTTP requests duration",
        ["worker_id", "method", "endpoint", "http_status"],
        registry=registry,
    )
    current_requests_gauge = Gauge(
        "http_requests_current",
        "Requests currently executing",
        ["worker_id", "method"],
        multiprocess_mode="liveall",
        registry=registry,
    )

    @application.middleware("http")
    async def add_metrics(request: Request, call_next: Any) -> Any:
        # Unfortunately we cannot get the route here because it has not yet been determined by fastapi,
        # so we only have a global gauge for all endpoints.
        current_requests_gauge.labels(WORKER_ID, request.method).inc()

        start_time = time.time()
        status_code = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            # starlette/fastapi handles exception first, so we should already get a proper response with a status here,
            # except for "unhandled" exceptions, which are handled at the outermost level and translated to 500
            status_code = status_code or HTTPStatus.INTERNAL_SERVER_ERROR.value

            if "route" in request.scope:
                endpoint = request.scope["root_path"] + request.scope["route"].path
            else:
                # We avoid to create an arbitrary number of metrics, by using for example the request path
                endpoint = "others"

            process_time = time.time() - start_time

            current_requests_gauge.labels(WORKER_ID, request.method).dec()

            request_counter.labels(WORKER_ID, request.method, endpoint, status_code).inc()
            request_duration_histo.labels(WORKER_ID, request.method, endpoint, status_code).observe(process_time)
        return response


def add_metrics(application: FastAPI, config: Config) -> None:
    """
    If configured, adds "/metrics" endpoint to report metrics to prometheus.
    Also registers metrics for HTTP requests.
    """
    prometheus_config = config.metrics.prometheus
    if not prometheus_config:
        return

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

    _add_metrics_middleware(prometheus_client.REGISTRY, application)


def _task_labels(task_type: TaskType, status: TaskStatus | None = None) -> list[str]:
    return [WORKER_ID, task_type.value.lower()] + ([status.name.lower()] if status else [])


class TasksMetricsRecorder(TaskServiceListener):
    """
    Exports metrics for tasks: wait time before execution, duration, ...
    """

    def __init__(self, registry: CollectorRegistry) -> None:
        self._duration_histo = Histogram(
            "tasks_duration_seconds",
            "Tasks duration in seconds",
            ["worker_id", "type", "status"],
            registry=registry,
        )
        self._wait_time_histo = Histogram(
            "tasks_wait_seconds",
            "Tasks wait time in seconds",
            ["worker_id", "type"],
            registry=registry,
        )
        self._running_gauge = Gauge(
            "tasks_running",
            "Count of running tasks",
            ["worker_id", "type"],
            multiprocess_mode="liveall",
            registry=registry,
        )
        self._pending_gauge = Gauge(
            "tasks_pending",
            "Count of pending tasks",
            ["worker_id", "type"],
            multiprocess_mode="liveall",
            registry=registry,
        )

        self._submit_times: dict[str, float] = {}
        self._start_times: dict[str, float] = {}

    @override
    def on_task_submit(self, task_id: str, task_type: TaskType) -> None:
        self._pending_gauge.labels(*_task_labels(task_type)).inc()
        self._submit_times[task_id] = time.time()

    @override
    def on_task_cancel(self, task_id: str, task_type: TaskType) -> None:
        labels = _task_labels(task_type)
        if task_id in self._submit_times:
            self._pending_gauge.labels(*labels).dec()
            self._wait_time_histo.labels(*labels).observe(time.time() - self._submit_times[task_id])
            del self._submit_times[task_id]

            # Adding one observation to duration histo as well, so that we can get stats
            # on actually cancelled tasks
            self._duration_histo.labels(*_task_labels(task_type, TaskStatus.CANCELLED)).observe(0)

    @override
    def on_task_start(self, task_id: str, task_type: TaskType) -> None:
        labels = _task_labels(task_type)
        self._pending_gauge.labels(*labels).dec()
        self._running_gauge.labels(*labels).inc()
        if task_id in self._submit_times:
            self._wait_time_histo.labels(*labels).observe(time.time() - self._submit_times[task_id])
            del self._submit_times[task_id]
        self._start_times[task_id] = time.time()

    @override
    def on_task_end(self, task_id: str, task_type: TaskType, task_status: TaskStatus) -> None:
        self._running_gauge.labels(*_task_labels(task_type)).dec()
        if task_id in self._start_times:
            self._duration_histo.labels(*_task_labels(task_type, task_status)).observe(
                time.time() - self._start_times[task_id]
            )
            del self._start_times[task_id]
