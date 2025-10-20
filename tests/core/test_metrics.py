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
import prometheus_client
from prometheus_client import CollectorRegistry, Metric
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from antarest.core.metrics import (
    TasksMetricsRecorder,
    _add_db_connection_metrics,
    _add_db_session_metrics,
)


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


def _get_histo_count(registry: CollectorRegistry, name: str) -> float | None:
    """
    Returns the count of values for a histogram metric.
    """
    count_sample_name = f"{name}_count"
    metric = _get_metric(registry, name)
    if not metric:
        return None
    try:
        sample = next(s for s in metric.samples if s.name == count_sample_name)
        return sample.value
    except StopIteration:
        return None


def test_task_metrics_recorder():
    metrics_registry = CollectorRegistry()
    recorder = TasksMetricsRecorder(metrics_registry)
    metrics = {m.name: m for m in metrics_registry.collect()}
    assert metrics.keys() == {"tasks_duration_seconds", "tasks_wait_seconds", "tasks_running", "tasks_pending"}

    recorder.on_task_submit("task1")
    metrics = {m.name: m for m in metrics_registry.collect()}
    assert metrics["tasks_running"].samples == []
    assert len(metrics["tasks_pending"].samples) == 1
    assert metrics["tasks_pending"].samples[0].value == 1
    assert metrics["tasks_duration_seconds"].samples == []
    assert metrics["tasks_wait_seconds"].samples == []

    recorder.on_task_start("task1")
    metrics = {m.name: m for m in metrics_registry.collect()}
    assert len(metrics["tasks_running"].samples) == 1
    assert metrics["tasks_running"].samples[0].value == 1
    assert len(metrics["tasks_pending"].samples) == 1
    assert metrics["tasks_pending"].samples[0].value == 0
    assert metrics["tasks_duration_seconds"].samples == []
    assert len(metrics["tasks_wait_seconds"].samples) > 0

    recorder.on_task_end("task1")
    metrics = {m.name: m for m in metrics_registry.collect()}
    assert len(metrics["tasks_running"].samples) == 1
    assert metrics["tasks_running"].samples[0].value == 0
    assert len(metrics["tasks_pending"].samples) == 1
    assert metrics["tasks_pending"].samples[0].value == 0
    assert len(metrics["tasks_duration_seconds"].samples) > 0
    assert len(metrics["tasks_wait_seconds"].samples) > 0


def test_db_connection_metrics():
    engine = create_engine("sqlite:///:memory:")

    registry = CollectorRegistry()
    _add_db_connection_metrics(registry, engine)

    metrics_names = {m.name for m in registry.collect()}
    assert metrics_names == {
        "dbconn_duration_seconds",
        "dbconn_in_use",
        "dbconn_checkout_count",
        "dbconn_checkin_count",
    }

    assert _get_value(registry, "dbconn_in_use") == 0

    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        conn.commit()

        assert _get_value(registry, "dbconn_in_use") == 1

    assert _get_value(registry, "dbconn_in_use") == 0
    assert _get_value(registry, "dbconn_checkout_count") == 1
    assert _get_value(registry, "dbconn_checkin_count") == 1
    assert _get_histo_count(registry, "dbconn_duration_seconds") == 1


def test_db_session_metrics():
    prometheus_client.disable_created_metrics()
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)

    registry = CollectorRegistry()
    _add_db_session_metrics(registry, session_factory)

    metrics_names = {m.name for m in registry.collect()}
    assert metrics_names == {
        "transaction_current",
        "transaction_duration_seconds",
        "dbsession_events",
    }

    assert _get_value(registry, "transaction_current") == 0
    assert _get_histo_count(registry, "transaction_duration_seconds") is None
    assert _get_value(registry, "dbsession_events", labels={"event_type": "begin"}) is None
    assert _get_value(registry, "dbsession_events", labels={"event_type": "rollback"}) is None
    assert _get_value(registry, "dbsession_events", labels={"event_type": "commit"}) is None

    with session_factory() as session:
        session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        assert _get_value(registry, "dbsession_events", labels={"event_type": "begin"}) == 1
        assert _get_value(registry, "dbsession_events", labels={"event_type": "rollback"}) is None
        assert _get_value(registry, "dbsession_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "transaction_current") == 1
        assert _get_histo_count(registry, "transaction_duration_seconds") is None

        session.rollback()
        assert _get_value(registry, "dbsession_events", labels={"event_type": "begin"}) == 1
        assert _get_value(registry, "dbsession_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "dbsession_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "transaction_current") == 0
        assert _get_histo_count(registry, "transaction_duration_seconds") == 1

    with session_factory() as session:
        session.execute(text("CREATE TABLE test2 (id INTEGER PRIMARY KEY)"))
        assert _get_value(registry, "dbsession_events", labels={"event_type": "begin"}) == 2
        assert _get_value(registry, "dbsession_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "dbsession_events", labels={"event_type": "commit"}) is None
        assert _get_value(registry, "transaction_current") == 1
        assert _get_histo_count(registry, "transaction_duration_seconds") == 1

        session.commit()
        assert _get_value(registry, "dbsession_events", labels={"event_type": "begin"}) == 2
        assert _get_value(registry, "dbsession_events", labels={"event_type": "rollback"}) == 1
        assert _get_value(registry, "dbsession_events", labels={"event_type": "commit"}) == 1
        assert _get_value(registry, "transaction_current") == 0
        assert _get_histo_count(registry, "transaction_duration_seconds") == 2
