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

import prometheus_client
import pytest
from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Metric
from pydantic import BaseModel
from sqlalchemy import Column, Integer, MetaData, QueuePool, Table, create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException
from starlette.testclient import TestClient

from antarest.core.metrics import (
    TasksMetricsRecorder,
    _add_db_connection_metrics,
    _add_db_session_metrics,
    _add_metrics_middleware,
)
from antarest.core.tasks.model import TaskStatus, TaskType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.main import add_exception_handlers


def _is_subset(small_dict: dict[str, str], big_dict: dict[str, str]) -> bool:
    return all(item in big_dict.items() for item in small_dict.items())


def _get_metric(registry: CollectorRegistry, name: str) -> Metric | None:
    try:
        return next(m for m in registry.collect() if m.name == name)
    except StopIteration:
        return None


def _get_value(registry: CollectorRegistry, name: str, labels: dict[str, str] | None = None) -> float | None:
    """
    Returns the value of the first (unique) sample of the metric matching the given name and labels.
    """
    metric = _get_metric(registry, name)
    if not metric:
        return None
    if not labels:
        return metric.samples[0].value if metric.samples else None
    else:
        try:
            sample = next(s for s in metric.samples if _is_subset(labels, s.labels))
            return sample.value
        except StopIteration:
            return None


def _get_histo_count(registry: CollectorRegistry, name: str, labels: dict[str, str] | None = None) -> float | None:
    """
    Returns the count of values for a histogram metric.
    """
    count_sample_name = f"{name}_count"
    metric = _get_metric(registry, name)
    if not metric:
        return None
    try:
        labels = labels or {}
        sample = next(s for s in metric.samples if s.name == count_sample_name and _is_subset(labels, s.labels))
        return sample.value
    except StopIteration:
        return None


def test_task_metrics_recorder():
    registry = CollectorRegistry()
    recorder = TasksMetricsRecorder(registry)
    metrics_names = {m.name for m in registry.collect()}
    assert metrics_names == {"tasks_duration_seconds", "tasks_wait_seconds", "tasks_running", "tasks_pending"}

    recorder.on_task_submit("task1", TaskType.ARCHIVE)
    assert _get_value(registry, "tasks_running", {"type": "archive"}) is None
    assert _get_value(registry, "tasks_pending", {"type": "archive"}) == 1
    assert _get_histo_count(registry, "tasks_wait_seconds", {"type": "archive"}) is None
    assert _get_histo_count(registry, "tasks_duration_seconds", {"type": "archive"}) is None

    recorder.on_task_start("task1", TaskType.ARCHIVE)
    assert _get_value(registry, "tasks_running", {"type": "archive"}) == 1
    assert _get_value(registry, "tasks_pending", {"type": "archive"}) == 0
    assert _get_histo_count(registry, "tasks_wait_seconds", {"type": "archive"}) == 1
    assert _get_histo_count(registry, "tasks_duration_seconds", {"type": "archive"}) is None

    recorder.on_task_end("task1", TaskType.ARCHIVE, TaskStatus.COMPLETED)
    assert _get_value(registry, "tasks_running", {"type": "archive"}) == 0
    assert _get_value(registry, "tasks_pending", {"type": "archive"}) == 0
    assert _get_histo_count(registry, "tasks_wait_seconds", {"type": "archive"}) == 1
    assert _get_histo_count(registry, "tasks_duration_seconds", {"type": "archive", "status": "completed"}) == 1


def test_cancelled_task_metrics():
    registry = CollectorRegistry()
    recorder = TasksMetricsRecorder(registry)

    recorder.on_task_submit("task1", TaskType.ARCHIVE)
    assert _get_value(registry, "tasks_running", {"type": "archive"}) is None
    assert _get_value(registry, "tasks_pending", {"type": "archive"}) == 1
    assert _get_histo_count(registry, "tasks_wait_seconds", {"type": "archive"}) is None
    assert _get_histo_count(registry, "tasks_duration_seconds", {"type": "archive"}) is None

    recorder.on_task_cancel("task1", TaskType.ARCHIVE)
    assert _get_value(registry, "tasks_running", {"type": "archive"}) is None
    assert _get_value(registry, "tasks_pending", {"type": "archive"}) == 0
    assert _get_histo_count(registry, "tasks_wait_seconds", {"type": "archive"}) == 1
    # We get one observation for cancelled tasks.
    assert _get_histo_count(registry, "tasks_duration_seconds", {"type": "archive", "status": "cancelled"}) == 1


def test_db_connection_metrics():
    engine = create_engine("sqlite:///:memory:")

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    metrics_names = {m.name for m in registry.collect()}
    assert metrics_names == {
        "db_connections_duration_seconds",
        "db_connections_used",
        "db_connections_idle",
        "db_connections_events",
    }

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 0

    with engine.connect() as conn:
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1
        conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        conn.commit()

        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 1
    assert _get_histo_count(registry, "db_connections_duration_seconds") == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) == 1


def test_db_connection_metrics_detach():
    engine = create_engine("sqlite:///:memory:")

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    with engine.connect() as conn:
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1
        conn.detach()

        assert _get_value(registry, "db_connections_used") == 0
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "detach"}) == 1

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 0
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) is None


def test_db_connection_metrics_overflow():
    engine = create_engine("sqlite:///:memory:", poolclass=QueuePool, max_overflow=1, pool_size=1)

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1

        # This connection will be an overflow connection
        with engine.connect():
            assert _get_value(registry, "db_connections_used") == 2
            assert _get_value(registry, "db_connections_idle") == 0
            # We get 1 more connect and 1 more checkout from the pool
            assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 2
            assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 2

    assert _get_value(registry, "db_connections_used") == 0
    # The overflow connection is checked in but closed instantly, we have only 1 idle connection
    assert _get_value(registry, "db_connections_idle") == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) == 2
    assert _get_value(registry, "db_connections_events", {"event_type": "close"}) == 1


def test_db_connection_metrics_invalidate():
    engine = create_engine("sqlite:///:memory:")

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    with engine.connect() as conn:
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "invalidate"}) is None
        conn.invalidate()

        assert _get_value(registry, "db_connections_used") == 0
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "invalidate"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "close"}) == 1

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 0
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) == 1

    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 2
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 2

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) == 2


def test_db_connection_metrics_recycle():
    engine = create_engine("sqlite:///:memory:", pool_recycle=1)

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 1

    time.sleep(1.1)

    # The underlying connection should be closed and recreated
    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 2
        assert _get_value(registry, "db_connections_events", {"event_type": "invalidate"}) is None
        assert _get_value(registry, "db_connections_events", {"event_type": "close"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 2

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 1
    assert _get_value(registry, "db_connections_events", {"event_type": "checkin"}) == 2


@pytest.mark.skip(reason="to be run manually with a local postgres server in debug mode")
def test_db_connection_metrics_preping():
    engine = create_engine("postgresql+psycopg2://postgres:somepass@127.0.0.1:5432/postgres", pool_pre_ping=True)

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0

    # Pause here and restart postgres server
    # With preping enabled, connections should be closed and recreated
    with engine.connect():
        assert _get_value(registry, "db_connections_used") == 1
        assert _get_value(registry, "db_connections_idle") == 0
        assert _get_value(registry, "db_connections_events", {"event_type": "connect"}) == 2
        assert _get_value(registry, "db_connections_events", {"event_type": "invalidate"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "close"}) == 1
        assert _get_value(registry, "db_connections_events", {"event_type": "checkout"}) == 2

    assert _get_value(registry, "db_connections_used") == 0
    assert _get_value(registry, "db_connections_idle") == 1


@pytest.mark.skip(reason="to be run manually with a local postgres server in debug mode")
def test_db_transaction_is_closed_on_server_disconnect():
    engine = create_engine("postgresql+psycopg2://postgres:somepass@127.0.0.1:5432/postgres", pool_pre_ping=True)

    session_factory = sessionmaker(bind=engine)

    registry = CollectorRegistry()
    _add_db_session_metrics(registry, session_factory)

    try:
        with db(session_factory):
            db.session.execute(text("DROP TABLE IF EXISTS test"))
            db.session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))

            # Put a breakpoint here and restart postgres server before continuing
            assert _get_value(registry, "db_transactions_current") == 1
    except Exception:
        pass

    # check that the DB transaction count is correctly decreased
    assert _get_value(registry, "db_transactions_current") == 0


def test_db_session_metrics():
    metadata = MetaData()

    prometheus_client.disable_created_metrics()
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)

    registry = CollectorRegistry()
    _add_db_session_metrics(registry, session_factory)

    metrics_names = {m.name for m in registry.collect()}
    assert metrics_names == {
        "db_transactions_current",
        "db_transactions_duration_seconds",
        "db_session_events",
    }

    assert _get_value(registry, "db_transactions_current") == 0
    assert _get_histo_count(registry, "db_transactions_duration_seconds") is None
    assert _get_value(registry, "db_session_events", labels={"event_type": "begin"}) is None
    assert _get_value(registry, "db_session_events", labels={"event_type": "rollback"}) is None
    assert _get_value(registry, "db_session_events", labels={"event_type": "commit"}) is None

    table = Table("test", metadata, Column("id", Integer, primary_key=True))

    with session_factory() as session:
        session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert _get_value(registry, "db_session_events", labels={"event_type": "begin"}) == 1
        assert _get_value(registry, "db_session_events", labels={"event_type": "rollback"}) is None
        assert _get_value(registry, "db_session_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "db_session_events", labels={"event_type": "select"}) is None
        assert _get_value(registry, "db_transactions_current") == 1
        assert _get_histo_count(registry, "db_transactions_duration_seconds") is None

        session.execute(table.select())
        assert _get_value(registry, "db_session_events", labels={"event_type": "select"}) == 1

        session.rollback()
        assert _get_value(registry, "db_session_events", labels={"event_type": "begin"}) == 1
        assert _get_value(registry, "db_session_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "db_session_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "db_transactions_current") == 0
        assert _get_histo_count(registry, "db_transactions_duration_seconds") == 1

    with session_factory() as session:
        session.execute(text("CREATE TABLE test2 (id INTEGER PRIMARY KEY)"))
        assert _get_value(registry, "db_session_events", labels={"event_type": "begin"}) == 2
        assert _get_value(registry, "db_session_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "db_session_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "db_transactions_current") == 1
        assert _get_histo_count(registry, "db_transactions_duration_seconds") == 1

        session.commit()
        assert _get_value(registry, "db_session_events", labels={"event_type": "begin"}) == 2
        assert _get_value(registry, "db_session_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "db_session_events", labels={"event_type": "commit"}) == 1
        assert _get_value(registry, "db_transactions_current") == 0
        assert _get_histo_count(registry, "db_transactions_duration_seconds") == 2


class DummyModel(BaseModel):
    value: int


def test_http_request_metrics() -> None:
    registry = CollectorRegistry()

    app = FastAPI()

    @app.get("/ok/{value}")
    def ok(value: str) -> None:
        pass

    @app.get("/notfound")
    def notfound() -> None:
        raise HTTPException(status_code=404)

    @app.get("/error")
    def error() -> None:
        raise Exception()

    @app.post("/validation")
    def validation(input: DummyModel) -> int:
        return input.value

    add_exception_handlers(app)

    _add_metrics_middleware(registry=registry, application=app)

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/ok/test")
    assert res.status_code == 200

    assert (
        _get_histo_count(
            registry, "http_requests_duration_seconds", labels={"http_status": "200", "endpoint": "/ok/{value}"}
        )
        == 1
    )

    res = client.get("/error")
    assert res.status_code == 500

    assert _get_histo_count(registry, "http_requests_duration_seconds", labels={"http_status": "500"}) == 1

    res = client.get("/notfound")
    assert res.status_code == 404
    assert _get_histo_count(registry, "http_requests_duration_seconds", labels={"http_status": "404"}) == 1

    res = client.post("/validation", json={"value": "invalid"})
    assert res.status_code == 422
    assert _get_histo_count(registry, "http_requests_duration_seconds", labels={"http_status": "422"}) == 1

    res = client.get("/doesnotexist")
    assert res.status_code == 404
    assert (
        _get_histo_count(
            registry,
            "http_requests_duration_seconds",
            labels={"method": "GET", "endpoint": "others", "http_status": "404"},
        )
        == 1
    )
