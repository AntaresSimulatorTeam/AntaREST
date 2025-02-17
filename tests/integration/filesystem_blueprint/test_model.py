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

import asyncio
import datetime
import re
from pathlib import Path

from pytest_mock import MockerFixture

from antarest.core.filesystem_blueprint import FileInfoDTO, FilesystemDTO, MountPointDTO


class TestFilesystemDTO:
    def test_init(self) -> None:
        example = {
            "name": "ws",
            "mount_dirs": {
                "default": "/path/to/workspaces/internal_studies",
                "common": "/path/to/workspaces/common_studies",
            },
        }
        dto = FilesystemDTO.model_validate(example)
        assert dto.name == example["name"]
        assert dto.mount_dirs["default"] == Path(example["mount_dirs"]["default"])
        assert dto.mount_dirs["common"] == Path(example["mount_dirs"]["common"])


class TestMountPointDTO:
    def test_init(self) -> None:
        example = {
            "name": "default",
            "path": "/path/to/workspaces/internal_studies",
            "total_bytes": 1e9,
            "used_bytes": 0.6e9,
            "free_bytes": 1e9 - 0.6e9,
            "message": f"{0.6e9 / 1e9:%} used",
        }
        dto = MountPointDTO.model_validate(example)
        assert dto.name == example["name"]
        assert dto.path == Path(example["path"])
        assert dto.total_bytes == example["total_bytes"]
        assert dto.used_bytes == example["used_bytes"]
        assert dto.free_bytes == example["free_bytes"]
        assert dto.message == example["message"]

    def test_from_path__missing_file(self) -> None:
        name = "foo"
        path = Path("/path/to/workspaces/internal_studies")
        dto = asyncio.run(MountPointDTO.from_path(name, path))
        assert dto.name == name
        assert dto.path == path
        assert dto.total_bytes == 0
        assert dto.used_bytes == 0
        assert dto.free_bytes == 0
        assert dto.message.startswith("N/A:"), dto.message

    def test_from_path__file(self, tmp_path: Path, mocker: MockerFixture) -> None:
        mocker.patch("shutil.disk_usage", return_value=(100, 200, 300))

        name = "foo"
        dto = asyncio.run(MountPointDTO.from_path(name, tmp_path))
        assert dto.name == name
        assert dto.path == tmp_path
        assert dto.total_bytes == 100
        assert dto.used_bytes == 200
        assert dto.free_bytes == 300
        assert re.fullmatch(r"\d+(?:\.\d+)?% used", dto.message), dto.message


class TestFileInfoDTO:
    def test_init(self) -> None:
        example = {
            "path": "/path/to/workspaces/internal_studies/5a503c20-24a3-4734-9cf8-89565c9db5ec/study.antares",
            "file_type": "file",
            "file_count": 1,
            "size_bytes": 126,
            "created": "2023-12-07T17:59:43",
            "modified": "2023-12-07T17:59:43",
            "accessed": "2024-01-11T17:54:09",
            "message": "OK",
        }
        dto = FileInfoDTO.model_validate(example)
        assert dto.path == Path(example["path"])
        assert dto.file_type == example["file_type"]
        assert dto.file_count == example["file_count"]
        assert dto.size_bytes == example["size_bytes"]
        assert dto.created == datetime.datetime.fromisoformat(example["created"])
        assert dto.modified == datetime.datetime.fromisoformat(example["modified"])
        assert dto.accessed == datetime.datetime.fromisoformat(example["accessed"])
        assert dto.message == example["message"]

    def test_from_path__missing_file(self) -> None:
        path = Path("/path/to/workspaces/internal_studies/5a503c20-24a3-4734-9cf8-89565c9db5ec/study.antares")
        dto = asyncio.run(FileInfoDTO.from_path(path))
        assert dto.path == path
        assert dto.file_type == "unknown"
        assert dto.file_count == 0
        assert dto.size_bytes == 0
        assert dto.created == datetime.datetime.min
        assert dto.modified == datetime.datetime.min
        assert dto.accessed == datetime.datetime.min
        assert dto.message.startswith("N/A:"), dto.message

    def test_from_path__file(self, tmp_path: Path) -> None:
        path = tmp_path / "foo.txt"
        before = datetime.datetime.now() - datetime.timedelta(seconds=1)
        path.write_bytes(b"1234567")  # 7 bytes
        after = datetime.datetime.now() + datetime.timedelta(seconds=1)
        dto = asyncio.run(FileInfoDTO.from_path(path))
        assert dto.path == path
        assert dto.file_type == "file"
        assert dto.file_count == 1
        assert dto.size_bytes == 7
        assert before <= dto.created <= after
        assert before <= dto.modified <= after
        assert before <= dto.accessed <= after
        assert dto.message == "OK"

    def test_from_path__directory(self, tmp_path: Path) -> None:
        path = tmp_path / "foo"
        before = datetime.datetime.now() - datetime.timedelta(seconds=1)
        path.mkdir()
        after = datetime.datetime.now() + datetime.timedelta(seconds=1)
        dto = asyncio.run(FileInfoDTO.from_path(path, details=False))
        assert dto.path == path
        assert dto.file_type == "directory"
        assert dto.file_count == 1
        assert dto.size_bytes == path.stat().st_size
        assert before <= dto.created <= after
        assert before <= dto.modified <= after
        assert before <= dto.accessed <= after
        assert dto.message == "OK"

    def test_from_path__directory_with_files(self, tmp_path: Path) -> None:
        path = tmp_path / "foo"
        before = datetime.datetime.now() - datetime.timedelta(seconds=1)
        path.mkdir()
        (path / "bar.txt").write_bytes(b"1234567")
        (path / "baz.txt").write_bytes(b"890")
        after = datetime.datetime.now() + datetime.timedelta(seconds=1)
        dto = asyncio.run(FileInfoDTO.from_path(path, details=True))
        assert dto.path == path
        assert dto.file_type == "directory"
        assert dto.file_count == 3
        assert dto.size_bytes == path.stat().st_size + 10
        assert before <= dto.created <= after
        assert before <= dto.modified <= after
        assert before <= dto.accessed <= after
        assert dto.message == "OK"
