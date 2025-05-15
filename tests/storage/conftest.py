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

import datetime
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union
from unittest.mock import Mock

import pytest

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownload
from antarest.core.filetransfer.repository import FileDownloadRepository
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.model import JSON
from antarest.core.tasks.model import CustomTaskEventMessages, TaskDTO, TaskListFilter, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService, NoopNotifier, Task


@pytest.fixture
def test_json_data() -> JSON:
    return {
        "part1": {"key_int": 1, "key_str": "value1"},
        "part2": {"key_bool": True, "key_bool2": False},
    }


@pytest.fixture
def lite_jsonschema() -> JSON:
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "properties": {
            "key_file1": {
                "type": "object",
                "rte-metadata": {"filename": "file1.ini"},
                "properties": {
                    "section": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "integer",
                                "title": "The params schema",
                            }
                        },
                    }
                },
            },
            "folder1": {
                "$id": "#/properties/folder1",
                "type": "object",
                "title": "The folder1 schema",
                "required": ["file2", "matrice1.txt", "folder2"],
                "properties": {
                    "file2": {
                        "type": "object",
                        "rte-metadata": {"filename": "file2.ini"},
                        "title": "The file3.ini schema",
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "type": "object",
                                "title": "The section schema",
                                "required": ["params"],
                                "properties": {
                                    "params": {
                                        "type": "integer",
                                        "title": "The params schema",
                                    }
                                },
                            }
                        },
                    },
                    "matrice1.txt": {
                        "$id": "#/properties/folder1/properties/matrice1.txt",
                        "type": "string",
                        "title": "The matrice1.txt schema",
                        "rte-metadata": {"filename": "matrice1.txt"},
                    },
                    "folder2": {
                        "$id": "#/properties/folder1/properties/folder2",
                        "type": "object",
                        "title": "The folder2 schema",
                        "required": ["matrice2.txt"],
                        "properties": {
                            "matrice2.txt": {
                                "$id": "#/properties/folder1/properties/folder2/properties/matrice2.txt",
                                "type": "string",
                                "title": "The matrice2.txt schema",
                                "rte-metadata": {"filename": "matrice2.txt"},
                            }
                        },
                    },
                },
            },
            "folder3": {
                "$id": "#/properties/folder3",
                "type": "object",
                "required": ["file3.ini"],
                "properties": {
                    "file3.ini": {
                        "type": "object",
                        "title": "The file3.ini schema",
                        "rte-metadata": {"filename": "file3.ini"},
                        "required": ["section"],
                        "properties": {
                            "section": {
                                "type": "object",
                                "title": "The section schema",
                                "required": ["params"],
                                "properties": {
                                    "params": {
                                        "type": "integer",
                                        "title": "The params schema",
                                    }
                                },
                            }
                        },
                    },
                    "areas": {
                        "type": "object",
                        "properties": {},
                        "rte-metadata": {"strategy": "S4"},
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "$id": {"type": "string"},
                                "matrice1.txt": {
                                    "type": "string",
                                    "rte-metadata": {"filename": "matrice1.txt"},
                                },
                                "file4.ini": {
                                    "type": "object",
                                    "required": ["section"],
                                    "rte-metadata": {"filename": "file4.ini"},
                                    "properties": {
                                        "section": {
                                            "type": "object",
                                            "required": ["params"],
                                            "properties": {
                                                "params": {
                                                    "type": "integer",
                                                }
                                            },
                                        }
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def lite_jsondata() -> JSON:
    file_content = {"section": {"params": 123}}
    return {
        "key_file1": file_content,
        "folder1": {
            "file2": file_content,
            "matrice1.txt": "file/root1/folder1/matrice1.txt",
            "folder2": {"matrice2.txt": "file/root1/folder1/folder2/matrice2.txt"},
        },
        "folder3": {
            "file3.ini": file_content,
            "areas": {
                "area1": {
                    "matrice1.txt": "file/root1/folder3/areas/area1/matrice1.txt",
                    "file4.ini": file_content,
                },
                "area2": {
                    "matrice1.txt": "file/root1/folder3/areas/area2/matrice1.txt",
                    "file4.ini": file_content,
                },
                "area3": {
                    "matrice1.txt": "file/root1/folder3/areas/area3/matrice1.txt",
                    "file4.ini": file_content,
                },
            },
        },
    }


@pytest.fixture
def lite_path(tmp_path: Path) -> Path:
    """
    root1
    |
    _ file1.ini
    |_folder1
        |_ file2.ini
        |_ matrice1.txt
        |_ folder2
            |_ matrice2.txt
    |_folder3
        |_ file3.ini
        |_ areas
            |_ area1
                |_ matrice3.txt
                |_ file4.ini
            |_ area2
                |_ matrice3.txt
                |_ file4.ini
            |_ area3
                |_ matrice3.txt
                |_ file4.ini
    """

    str_content_ini = """
        [section]
        params = 123
    """

    path = Path(tmp_path) / "root1"
    path_folder = Path(path)
    path_folder.mkdir()
    (path / "file1.ini").write_text(str_content_ini)
    path /= "folder1"
    path.mkdir()
    (path / "file2.ini").write_text(str_content_ini)
    (path / "matrice1.txt").touch()
    path /= "folder2"
    path.mkdir()
    (path / "matrice2.txt").touch()
    path = Path(path_folder) / "folder3"
    path.mkdir()
    (path / "file3.ini").write_text(str_content_ini)

    path /= "areas"
    path.mkdir()

    def create_area(path_areas: Path, area: str) -> None:
        path_area = path_areas / area
        path_area.mkdir()
        (path_area / "file4.ini").write_text(str_content_ini)
        (path_area / "matrice1.txt").touch()

    create_area(path, "area1")
    create_area(path, "area2")
    create_area(path, "area3")

    return path_folder


class SimpleSyncTaskService(ITaskService):
    def add_worker_task(
        self,
        task_type: TaskType,
        task_queue: str,
        task_args: Dict[str, Union[int, float, bool, str]],
        name: Optional[str],
        ref_id: Optional[str],
    ) -> Optional[str]:
        raise NotImplementedError()

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
            creation_date_utc=datetime.datetime.now().isoformat(" "),
            completion_date_utc=None,
            result=None,
            logs=None,
        )

    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        return []

    def await_task(self, task_id: str, timeout_sec: Optional[int] = None) -> None:
        pass


class FileDownloadRepositoryMock(FileDownloadRepository):
    def __init__(self) -> None:
        self.downloads: Dict[str, FileDownload] = {}

    def add(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    def get(self, download_id: str) -> Optional[FileDownload]:
        return self.downloads.get(download_id, None)

    def save(self, download: FileDownload) -> None:
        self.downloads[download.id] = download

    def get_all(self, owner: Optional[int] = None) -> List[FileDownload]:
        return list(self.downloads.values())


class SimpleFileTransferManager(FileTransferManager):
    def __init__(self, config: Config):
        super().__init__(FileDownloadRepositoryMock(), Mock(), config)
