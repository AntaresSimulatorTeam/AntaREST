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

"""Task action handlers for study operations."""

from __future__ import annotations

import logging
import os
from pathlib import Path, PurePosixPath
from typing import Any

from antares.study.version import StudyVersion

from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo
from antarest.core.tasks.action import TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.archives import ArchiveFormat
from antarest.login.utils import get_user_id
from antarest.service_creator import CoreServices
from antarest.study.service import assert_raw
from antarest.study.storage.utils import remove_from_cache

logger = logging.getLogger(__name__)


@TaskActionRegistry.register("archive_study")
def handle_archive_study(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    uuid = params["study_id"]
    study_to_archive = study_service.get_study(uuid)
    study_to_archive = assert_raw(study_to_archive)
    study_service.storage_service.raw_study_service.archive(study_to_archive)
    study_to_archive.archived = True
    study_service.repository.save(study_to_archive)
    study_service.event_bus.push(
        Event(
            type=EventType.STUDY_EDITED,
            payload=study_to_archive.to_json_summary(),
            permissions=PermissionInfo.from_study(study_to_archive),
        )
    )
    return TaskResult(success=True, message="ok")


@TaskActionRegistry.register("unarchive_study")
def handle_unarchive_study(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    uuid = params["study_id"]
    study_to_unarchive = study_service.get_study(uuid)
    study_to_unarchive = assert_raw(study_to_unarchive)
    study_service.storage_service.raw_study_service.unarchive(study_to_unarchive)
    study_to_unarchive.archived = False

    os.unlink(study_service.storage_service.raw_study_service.find_archive_path(study_to_unarchive))
    study_service.repository.save(study_to_unarchive)
    study_service.event_bus.push(
        Event(
            type=EventType.STUDY_EDITED,
            payload=study_to_unarchive.to_json_summary(),
            permissions=PermissionInfo.from_study(study_to_unarchive),
        )
    )
    remove_from_cache(cache=study_service.cache_service, root_id=uuid)
    return TaskResult(success=True, message="ok")


@TaskActionRegistry.register("copy_study")
def handle_copy_study(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    src_uuid = params["src_uuid"]
    dest_study_name = params["dest_study_name"]
    group_ids = params["group_ids"]
    destination_folder = (
        PurePosixPath(params["destination_folder"]) if params.get("destination_folder") else PurePosixPath()
    )
    output_ids = params.get("output_ids", [])
    with_outputs = params.get("with_outputs")
    owner_id = params.get("owner_id")
    group_entity_ids = params.get("group_entity_ids", [])

    origin_study = study_service.get_study(src_uuid)
    study = study_service.storage_service.get_storage(origin_study).copy(
        origin_study,
        dest_study_name,
        group_ids,
        destination_folder,
        output_ids,
        with_outputs,
    )

    if owner_id is not None:
        study.owner = study_service.user_service.get_user(owner_id)
    if group_entity_ids:
        study.groups = [study_service.user_service.get_group(gid) for gid in group_entity_ids]

    study_service._save_study(study)
    study_service.storage_service.raw_study_service.normalize_study(study)

    # Copying all jobs associated with the study
    jobs = study_service.job_result_repository.find_by_study_and_output_ids(origin_study.id, output_ids)
    new_jobs = [job.copy_jobs_for_study(study.id) for job in jobs]
    if new_jobs:
        study_service.job_result_repository.save_all(new_jobs)

    study_service.event_bus.push(
        Event(
            type=EventType.STUDY_CREATED,
            payload=study.to_json_summary(),
            permissions=PermissionInfo.from_study(study),
        )
    )

    logger.info(
        "study %s copied to %s by user %s",
        origin_study,
        study.id,
        get_user_id(),
    )
    return TaskResult(
        success=True,
        message=f"Study {src_uuid} successfully copied to {study.id}",
        return_value=study.id,
    )


@TaskActionRegistry.register("export_study")
def handle_export_study(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    uuid = params["study_id"]
    outputs = params["outputs"]
    archive_format = ArchiveFormat(params["archive_format"])
    export_path = Path(params["export_path"])
    export_id = params["export_id"]

    try:
        target_study = study_service.get_study(uuid)
        study_service.storage_service.get_storage(target_study).export_study(
            target_study, export_path, outputs, archive_format
        )
        study_service.file_transfer_manager.set_ready(export_id)
        return TaskResult(success=True, message=f"Study {uuid} successfully exported")
    except Exception as e:
        study_service.file_transfer_manager.fail(export_id, str(e))
        raise e


@TaskActionRegistry.register("generate_timeseries")
def handle_generate_timeseries(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    from antarest.study.service import ThermalClusterTimeSeriesGeneratorTask

    study_service = services.study_service
    study_id = params["study_id"]
    outage_details = params["outage_details"]

    task = ThermalClusterTimeSeriesGeneratorTask(
        study_id,
        repository=study_service.repository,
        storage_service=study_service.storage_service,
        event_bus=study_service.event_bus,
        study_interface_supplier=study_service.get_study_interface,
        thermal_outage_details=outage_details,
    )
    return task.run_task(notifier)


@TaskActionRegistry.register("upgrade_study")
def handle_upgrade_study(services: CoreServices, params: dict[str, Any], notifier: ITaskNotifier) -> TaskResult:
    from antarest.study.service import StudyUpgraderTask

    study_service = services.study_service
    study_id = params["study_id"]
    target_version = StudyVersion.parse(params["target_version"])

    task = StudyUpgraderTask(
        study_id,
        target_version,
        repository=study_service.repository,
        storage_service=study_service.storage_service,
        cache_service=study_service.cache_service,
        event_bus=study_service.event_bus,
    )
    return task.run_task(notifier)
