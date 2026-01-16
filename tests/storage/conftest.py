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

import uuid
from typing import Dict, List, Optional
from unittest.mock import Mock

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownload
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskListFilter, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService, NoopNotifier, Task
from antarest.core.utils.utils import current_time


class SimpleSyncTaskService(ITaskService):
    @override
    def add_task(
        self,
        action: Task,
        name: Optional[str],
        task_type: Optional[TaskType],
        ref_id: Optional[str],
        progress: Optional[int],
        custom_event_messages: Optional[CustomTaskEventMessages],
    ) -> str:
        action(NoopNotifier())
        return str(uuid.uuid4())

    @override
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        return TaskDTO(
            id=task_id,
            name="mock",
            owner=None,
            status=TaskStatus.COMPLETED,
            creation_date_utc=current_time().isoformat(" "),
            completion_date_utc=None,
            result=None,
            logs=None,
        )

    @override
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        return []

    @override
    def await_task(self, task_id: str, timeout_sec: Optional[int] = None) -> None:
        pass


class FileDownloadRepositoryMock(FileDownloadRepository):
    def __init__(self) -> None:
        self.downloads: Dict[str, FileDownload] = {}

    @override
    def add(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    @override
    def get(self, download_id: str) -> Optional[FileDownload]:
        return self.downloads.get(download_id, None)

    @override
    def save(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    @override
    def get_all(self, owner: Optional[int] = None) -> List[FileDownload]:
        return list(self.downloads.values())


class SimpleFileTransferManager(FileTransferManager):
    def __init__(self, config: Config):
        super().__init__(FileDownloadRepositoryMock(), Mock(), config)
