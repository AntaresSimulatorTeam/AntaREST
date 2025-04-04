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
from pathlib import Path
from typing import Optional

from antarest.core.config import DEFAULT_WORKSPACE_NAME
from antarest.core.exceptions import OutputAlreadyUnarchived, OutputNotFound, TaskAlreadyRunning
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskNotifier
from antarest.core.utils.archives import ArchiveFormat
from antarest.core.utils.utils import StopWatch
from antarest.study.model import Study
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)
from antarest.study.storage.utils import assert_permission, is_output_archived
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)


class OutputService:
    def __init__(self, study_service: StudyService):
        self.study_service = study_service

    def get_digest_file(self, study_id: str, output_id: str, params: RequestParameters) -> DigestUI:
        study = self.study_service.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        file_study = self.study_service.storage_service.get_storage(study).get_raw(study)
        digest_node = file_study.tree.get_node(url=["output", output_id, "economy", "mc-all", "grid", "digest"])
        assert isinstance(digest_node, DigestSynthesis)
        return digest_node.get_ui()

    @staticmethod
    def _get_output_archive_task_names(study: Study, output_id: str) -> tuple[str, str]:
        return (
            f"Archive output {study.id}/{output_id}",
            f"Unarchive output {study.name}/{output_id} ({study.id})",
        )

    def unarchive_output(
        self,
        study_id: str,
        output_id: str,
        keep_src_zip: bool,
        params: RequestParameters,
    ) -> Optional[str]:
        study = self.study_service.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self.study_service.assert_study_unarchived(study)

        output_path = Path(study.path) / "output" / output_id
        if not is_output_archived(output_path):
            if not output_path.exists():
                raise OutputNotFound(output_id)
            raise OutputAlreadyUnarchived(output_id)

        archive_task_names = OutputService._get_output_archive_task_names(study, output_id)
        task_name = archive_task_names[1]

        study_tasks = self.study_service.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        if len(list(filter(lambda t: t.name in archive_task_names, study_tasks))):
            raise TaskAlreadyRunning()

        def unarchive_output_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                study = self.study_service.get_study(study_id)
                stopwatch = StopWatch()
                self.study_service.storage_service.get_storage(study).unarchive_study_output(
                    study, output_id, keep_src_zip
                )
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Output {output_id} of study {study_id} unarchived in {x}s")
                )
                return TaskResult(
                    success=True,
                    message=f"Study output {study_id}/{output_id} successfully unarchived",
                )
            except Exception as e:
                logger.warning(
                    f"Could not unarchive the output {study_id}/{output_id}",
                    exc_info=e,
                )
                raise e

        task_id: Optional[str] = None
        workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
        if workspace != DEFAULT_WORKSPACE_NAME:
            dest = Path(study.path) / "output" / output_id
            src = Path(study.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}"
            task_id = self.study_service.task_service.add_worker_task(
                TaskType.UNARCHIVE,
                f"unarchive_{workspace}",
                ArchiveTaskArgs(
                    src=str(src),
                    dest=str(dest),
                    remove_src=not keep_src_zip,
                ).model_dump(mode="json"),
                name=task_name,
                ref_id=study.id,
                request_params=params,
            )

        if not task_id:
            task_id = self.study_service.task_service.add_task(
                unarchive_output_task,
                task_name,
                task_type=TaskType.UNARCHIVE,
                ref_id=study.id,
                progress=None,
                custom_event_messages=None,
                request_params=params,
            )

        return task_id
