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
from prometheus_client import CollectorRegistry

from antarest.core.metrics import TasksMetricsRecorder


def test_task_metric_srecorder():
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
