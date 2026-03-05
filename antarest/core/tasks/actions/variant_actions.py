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

"""Task action handlers for variant study operations."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from antarest.core.tasks.action import TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


@TaskActionRegistry.register("generate_variant")
def handle_generate_variant(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    variant_service = services.study_service.storage_service.variant_study_service
    study_id = params["study_id"]
    denormalize = params.get("denormalize", False)
    from_scratch = params.get("from_scratch", False)

    from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator

    generator = SnapshotGenerator(
        cache=variant_service.cache,
        raw_study_service=variant_service.raw_study_service,
        command_factory=variant_service.command_factory,
        study_factory=variant_service.study_factory,
        repository=variant_service.repository,
    )
    generate_result = generator.generate_snapshot(
        study_id,
        denormalize=denormalize,
        from_scratch=from_scratch,
        notifier=notifier,
        listener=None,
    )
    return TaskResult(
        success=generate_result.success,
        message=(f"{study_id} generated successfully" if generate_result.success else f"{study_id} not generated"),
        return_value=generate_result.model_dump_json(),
    )


@TaskActionRegistry.register("clear_all_snapshots")
def handle_clear_all_snapshots(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    variant_service = services.study_service.storage_service.variant_study_service
    retention_seconds = params["retention_seconds"]
    retention_time = timedelta(seconds=retention_seconds)

    from antarest.study.storage.variantstudy.variant_study_service import SnapshotCleanerTask

    task = SnapshotCleanerTask(variant_study_service=variant_service, retention_time=retention_time)
    return task.run_task(notifier)
