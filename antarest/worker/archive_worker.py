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

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.serde import AntaresBaseModel
from antarest.core.tasks.model import TaskResult
from antarest.core.utils.archives import unzip
from antarest.core.utils.utils import StopWatch
from antarest.worker.worker import AbstractWorker, WorkerTaskCommand

logger = logging.getLogger(__name__)


class ArchiveTaskArgs(AntaresBaseModel):
    src: str
    dest: str
    remove_src: bool = False


class ArchiveWorker(AbstractWorker):
    """
    The Antares archive worker is a task that runs in the background$
    to automatically unarchive simulation results.

    The worker is notified by the web application via EventBus to initiate
    asynchronous unarchiving of the results.
    """

    TASK_TYPE = "unarchive"

    def __init__(
        self,
        event_bus: IEventBus,
        workspace: str,
        local_root: Path,
        config: Config,
    ):
        self.workspace = workspace
        self.config = config
        self.local_root = local_root
        super().__init__(
            "Unarchive worker",
            event_bus,
            [f"{ArchiveWorker.TASK_TYPE}_{workspace}"],
        )

    @override
    def _execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        logger.info(f"Executing task {task_info.model_dump_json()}")
        try:
            # sourcery skip: extract-method
            archive_args = ArchiveTaskArgs.model_validate(task_info.task_args)
            dest = self.translate_path(Path(archive_args.dest))
            src = self.translate_path(Path(archive_args.src))
            stopwatch = StopWatch()
            logger.info(f"Extracting {src} into {dest}")
            unzip(
                dest,
                src,
                remove_source_zip=archive_args.remove_src,
            )
            stopwatch.log_elapsed(lambda t: logger.info(f"Successfully extracted {src} into {dest} in {t}s"))
            return TaskResult(success=True, message="")
        except Exception as e:
            logger.warning(
                f"Task {task_info.model_dump_json()} failed",
                exc_info=e,
            )
            return TaskResult(success=False, message=str(e))

    def translate_path(self, path: Path) -> Path:
        workspace = self.config.storage.workspaces[self.workspace]
        return self.local_root / path.relative_to(workspace.path)
