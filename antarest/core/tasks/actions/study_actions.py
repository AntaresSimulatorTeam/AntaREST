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
from typing import Optional

from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo
from antarest.core.tasks.action import TaskActionParams, TaskActionRegistry
from antarest.core.tasks.model import TaskResult
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.archives import ArchiveFormat
from antarest.login.utils import get_user_id
from antarest.service_creator import CoreServices
from antarest.study.service import assert_raw
from antarest.study.storage.utils import remove_from_cache

logger = logging.getLogger(__name__)


class ArchiveStudyParams(TaskActionParams):
    study_id: str


class UnarchiveStudyParams(TaskActionParams):
    study_id: str


class CopyStudyParams(TaskActionParams):
    src_uuid: str
    dest_study_name: str
    group_ids: list[str]
    destination_folder: Optional[str] = None
    output_ids: list[str] = []
    with_outputs: Optional[bool] = None
    owner_id: Optional[int] = None
    group_entity_ids: list[str] = []


class ExportStudyParams(TaskActionParams):
    study_id: str
    outputs: bool
    archive_format: str
    export_path: str
    export_id: str


class GenerateTimeseriesParams(TaskActionParams):
    study_id: str
    outage_details: bool


class UpgradeStudyParams(TaskActionParams):
    study_id: str
    target_version: str


@TaskActionRegistry.register("archive_study", ArchiveStudyParams)
def handle_archive_study(services: CoreServices, params: ArchiveStudyParams, notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    study_to_archive = study_service.get_study(params.study_id)
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


@TaskActionRegistry.register("unarchive_study", UnarchiveStudyParams)
def handle_unarchive_study(services: CoreServices, params: UnarchiveStudyParams, notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    study_to_unarchive = study_service.get_study(params.study_id)
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
    remove_from_cache(cache=study_service.cache_service, root_id=params.study_id)
    return TaskResult(success=True, message="ok")


@TaskActionRegistry.register("copy_study", CopyStudyParams)
def handle_copy_study(services: CoreServices, params: CopyStudyParams, notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    destination_folder = PurePosixPath(params.destination_folder) if params.destination_folder else PurePosixPath()

    origin_study = study_service.get_study(params.src_uuid)
    study = study_service.storage_service.get_storage(origin_study).copy(
        origin_study,
        params.dest_study_name,
        params.group_ids,
        destination_folder,
        params.output_ids,
        params.with_outputs,
    )

    if params.owner_id is not None:
        study.owner = study_service.user_service.get_user(params.owner_id)
    if params.group_entity_ids:
        study.groups = [study_service.user_service.get_group(gid) for gid in params.group_entity_ids]

    study_service._save_study(study)
    study_service.storage_service.raw_study_service.normalize_study(study)

    # Copying all jobs associated with the study
    jobs = study_service.job_result_repository.find_by_study_and_output_ids(origin_study.id, params.output_ids)
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
        message=f"Study {params.src_uuid} successfully copied to {study.id}",
        return_value=study.id,
    )


@TaskActionRegistry.register("export_study", ExportStudyParams)
def handle_export_study(services: CoreServices, params: ExportStudyParams, notifier: ITaskNotifier) -> TaskResult:
    study_service = services.study_service
    archive_format = ArchiveFormat(params.archive_format)
    export_path = Path(params.export_path)

    try:
        target_study = study_service.get_study(params.study_id)
        study_service.storage_service.get_storage(target_study).export_study(
            target_study, export_path, params.outputs, archive_format
        )
        study_service.file_transfer_manager.set_ready(params.export_id)
        return TaskResult(success=True, message=f"Study {params.study_id} successfully exported")
    except Exception as e:
        study_service.file_transfer_manager.fail(params.export_id, str(e))
        raise e


@TaskActionRegistry.register("generate_timeseries", GenerateTimeseriesParams)
def handle_generate_timeseries(
    services: CoreServices, params: GenerateTimeseriesParams, notifier: ITaskNotifier
) -> TaskResult:
    from antarest.study.service import ThermalClusterTimeSeriesGeneratorTask

    study_service = services.study_service

    task = ThermalClusterTimeSeriesGeneratorTask(
        params.study_id,
        repository=study_service.repository,
        storage_service=study_service.storage_service,
        event_bus=study_service.event_bus,
        study_interface_supplier=study_service.get_study_interface,
        thermal_outage_details=params.outage_details,
    )
    return task.run_task(notifier)


@TaskActionRegistry.register("upgrade_study", UpgradeStudyParams)
def handle_upgrade_study(services: CoreServices, params: UpgradeStudyParams, notifier: ITaskNotifier) -> TaskResult:
    from antares.study.version import StudyVersion

    from antarest.study.service import StudyUpgraderTask

    study_service = services.study_service
    target_version = StudyVersion.parse(params.target_version)

    task = StudyUpgraderTask(
        params.study_id,
        target_version,
        repository=study_service.repository,
        storage_service=study_service.storage_service,
        cache_service=study_service.cache_service,
        event_bus=study_service.event_bus,
    )
    return task.run_task(notifier)
