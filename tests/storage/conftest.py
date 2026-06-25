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
from unittest.mock import Mock

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownload
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskListFilter, TaskStatus, TaskType
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, ITaskService, NoopNotifier, Task
from antarest.core.utils.utils import current_time


class SimpleSyncTaskService(ITaskService):
    @override
    def add_task(
        self,
        action: Task,
        name: str | None,
        task_type: TaskType | None,
        ref_id: str | None,
        progress: int | None,
        custom_event_messages: CustomTaskEventMessages | None,
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
    def list_tasks(self, task_filter: TaskListFilter) -> list[TaskDTO]:
        return []

    @override
    def await_task(self, task_id: str, timeout_sec: int | None = None) -> None:
        pass

    @override
    async def await_task_async(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        pass

    @override
    def cancel_task(self, task_id: str) -> None:
        pass

    @override
    def get_task_progress(self, task_id: str) -> int | None:
        return None

    @override
    def delete_task_by_creation_date(self, task_retention_duration: int) -> int:
        pass


class FileDownloadRepositoryMock(FileDownloadRepository):
    def __init__(self) -> None:
        self.downloads: dict[str, FileDownload] = {}

    @override
    def add(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    @override
    def get(self, download_id: str) -> FileDownload | None:
        return self.downloads.get(download_id, None)

    @override
    def save(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    @override
    def get_all(self, owner: int | None = None) -> list[FileDownload]:
        return list(self.downloads.values())


class SimpleFileTransferManager(FileTransferManager):
    def __init__(self, config: Config):
        super().__init__(FileDownloadRepositoryMock(), Mock(), config)
