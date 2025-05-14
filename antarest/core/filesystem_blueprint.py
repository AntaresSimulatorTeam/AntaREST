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

"""
Filesystem Blueprint
"""

import asyncio
import datetime
import os
import shutil
import stat
from pathlib import Path
from typing import Iterator, Mapping, Sequence, Tuple, TypeAlias

import typing_extensions as te
from fastapi import APIRouter, HTTPException
from pydantic import Field
from starlette.responses import PlainTextResponse, StreamingResponse

from antarest.core.config import Config
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth

FilesystemName: TypeAlias = te.Annotated[str, Field(pattern=r"^\w+$", description="Filesystem name")]
MountPointName: TypeAlias = te.Annotated[str, Field(pattern=r"^\w+$", description="Mount point name")]


class FilesystemDTO(
    AntaresBaseModel,
    extra="forbid",
    json_schema_extra={
        "example": {
            "name": "ws",
            "mount_dirs": {
                "default": "/path/to/workspaces/internal_studies",
                "common": "/path/to/workspaces/common_studies",
            },
        },
    },
):
    """
    Filesystem information.

    Attributes:

    - `name`: name of the filesystem.
    - `mount_dirs`: mapping of the mount point names to their full path in Antares Web Server.
    """

    name: FilesystemName
    mount_dirs: Mapping[str, Path] = Field(description="Full path of the mount points in Antares Web Server")


class MountPointDTO(
    AntaresBaseModel,
    extra="forbid",
    json_schema_extra={
        "example": {
            "name": "default",
            "path": "/path/to/workspaces/internal_studies",
            "total_bytes": 1e9,
            "used_bytes": 0.6e9,
            "free_bytes": 1e9 - 0.6e9,
            "message": f"{0.6e9 / 1e9:%} used",
        },
    },
):
    """
    Disk usage information of a filesystem.

    Attributes:

    - `name`: name of the mount point.
    - `path`: path of the mount point.
    - `total_bytes`: total size of the mount point in bytes.
    - `used_bytes`: used size of the mount point in bytes.
    - `free_bytes`: free size of the mount point in bytes.
    - `message`: a message describing the status of the mount point.
    """

    name: MountPointName
    path: Path = Field(description="Full path of the mount point in Antares Web Server")
    total_bytes: int = Field(default=0, description="Total size of the mount point in bytes")
    used_bytes: int = Field(default=0, description="Used size of the mount point in bytes")
    free_bytes: int = Field(default=0, description="Free size of the mount point in bytes")
    message: str = Field(default="", description="A message describing the status of the mount point")

    @classmethod
    async def from_path(cls, name: str, path: Path) -> "MountPointDTO":
        obj = cls(name=name, path=path)
        try:
            obj.total_bytes, obj.used_bytes, obj.free_bytes = shutil.disk_usage(obj.path)
        except OSError as exc:
            # Avoid raising an exception if the file doesn't exist
            # or if the mount point is not available.
            obj.message = f"N/A: {exc}"
        else:
            obj.message = f"{obj.used_bytes / obj.total_bytes:.1%} used"
        return obj


class FileInfoDTO(
    AntaresBaseModel,
    extra="forbid",
    json_schema_extra={
        "example": {
            "path": "/path/to/workspaces/internal_studies/5a503c20-24a3-4734-9cf8-89565c9db5ec/study.antares",
            "file_type": "file",
            "file_count": 1,
            "size_bytes": 126,
            "created": "2023-12-07T17:59:43",
            "modified": "2023-12-07T17:59:43",
            "accessed": "2024-01-11T17:54:09",
            "message": "OK",
        },
    },
):
    """
    File information of a file or directory.

    Attributes:

    - `path`: full path of the file or directory in Antares Web Server.
    - `file_type`: file type: "directory", "file", "symlink", "socket", "block_device",
      "character_device", "fifo", or "unknown".
    - `file_count`: number of files and folders in the directory (1 for files).
    - `size_bytes`: size of the file or total size of the directory in bytes.
    - `created`: creation date of the file or directory (local time).
    - `modified`: last modification date of the file or directory (local time).
    - `accessed`: last access date of the file or directory (local time).
    - `message`: a message describing the status of the file.
    """

    path: Path = Field(description="Full path of the file or directory in Antares Web Server")
    file_type: str = Field(description="Type of the file or directory")
    file_count: int = Field(default=1, description="Number of files and folders in the directory (1 for files)")
    size_bytes: int = Field(default=0, description="Size of the file or total size of the directory in bytes")
    created: datetime.datetime = Field(description="Creation date of the file or directory (local time)")
    modified: datetime.datetime = Field(description="Last modification date of the file or directory (local time)")
    accessed: datetime.datetime = Field(description="Last access date of the file or directory (local time)")
    message: str = Field(default="OK", description="A message describing the status of the file")

    @classmethod
    async def from_path(cls, full_path: Path, *, details: bool = False) -> "FileInfoDTO":
        try:
            file_stat = full_path.stat()
        except OSError as exc:
            # Avoid raising an exception if the file doesn't exist
            # or if the mount point is not available.
            return cls(
                path=full_path,
                file_type="unknown",
                file_count=0,  # missing
                size_bytes=0,  # missing
                created=datetime.datetime.min,
                modified=datetime.datetime.min,
                accessed=datetime.datetime.min,
                message=f"N/A: {exc}",
            )

        obj = cls(
            path=full_path,
            file_type="unknown",
            file_count=1,
            size_bytes=file_stat.st_size,
            created=datetime.datetime.fromtimestamp(file_stat.st_ctime),
            modified=datetime.datetime.fromtimestamp(file_stat.st_mtime),
            accessed=datetime.datetime.fromtimestamp(file_stat.st_atime),
            message="OK",
        )

        if stat.S_ISDIR(file_stat.st_mode):
            obj.file_type = "directory"
            if details:
                file_count, disk_space = await _calc_details(full_path)
                obj.file_count = file_count
                obj.size_bytes = disk_space
        elif stat.S_ISREG(file_stat.st_mode):
            obj.file_type = "file"
        elif stat.S_ISLNK(file_stat.st_mode):  # pragma: no cover
            obj.file_type = "symlink"
        elif stat.S_ISSOCK(file_stat.st_mode):  # pragma: no cover
            obj.file_type = "socket"
        elif stat.S_ISBLK(file_stat.st_mode):  # pragma: no cover
            obj.file_type = "block_device"
        elif stat.S_ISCHR(file_stat.st_mode):  # pragma: no cover
            obj.file_type = "character_device"
        elif stat.S_ISFIFO(file_stat.st_mode):  # pragma: no cover
            obj.file_type = "fifo"
        else:  # pragma: no cover
            obj.file_type = "unknown"

        return obj


async def _calc_details(full_path: str | Path) -> Tuple[int, int]:
    """Calculate the number of files and the total size of a directory recursively."""

    full_path = Path(full_path)
    file_stat = full_path.stat()
    file_count = 1
    total_size = file_stat.st_size

    if stat.S_ISDIR(file_stat.st_mode):
        for entry in os.scandir(full_path):
            sub_file_count, sub_total_size = await _calc_details(entry.path)
            file_count += sub_file_count
            total_size += sub_total_size

    return file_count, total_size


def _is_relative_to(path: Path, base_path: Path) -> bool:
    """Check if the given path is relative to the specified base path."""
    try:
        path = Path(path).resolve()
        base_path = Path(base_path).resolve()
        return bool(path.relative_to(base_path))
    except ValueError:
        return False


def create_file_system_blueprint(config: Config) -> APIRouter:
    """
    Create the blueprint for the file system API.

    This blueprint is used to diagnose the disk space consumption of the different
    workspaces (especially the "default" workspace of Antares Web), and the different
    storage directories (`tmp`, `matrixstore`, `archive`, etc. defined in the configuration file).

    This blueprint is also used to list files and directories, and to view or download a file.

    Reading files is allowed for authenticated users, but deleting files is reserved
    for site administrators.

    Args:
        config: Application configuration.

    Returns:
        The blueprint.
    """
    auth = Auth(config)
    bp = APIRouter(
        prefix="/v1/filesystem",
        tags=[APITag.filesystem],
        dependencies=[auth.required()],
        include_in_schema=True,  # but may be disabled in the future
    )
    config_dirs = {
        "res": config.resources_path,
        "tmp": config.storage.tmp_dir,
        "matrix": config.storage.matrixstore,
        "archive": config.storage.archive_dir,
    }
    workspace_dirs = {name: ws_cfg.path for name, ws_cfg in config.storage.workspaces.items()}
    filesystems = {
        "cfg": config_dirs,
        "ws": workspace_dirs,
    }

    # Utility functions
    # =================

    def _get_mount_dirs(fs: str) -> Mapping[str, Path]:
        try:
            return filesystems[fs]
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Filesystem not found: '{fs}'") from None

    def _get_mount_dir(fs: str, mount: str) -> Path:
        try:
            return filesystems[fs][mount]
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Mount point not found: '{fs}/{mount}'") from None

    def _get_full_path(mount_dir: Path, path: str) -> Path:
        if not path:
            raise HTTPException(status_code=400, detail="Empty or missing path parameter")
        full_path = (mount_dir / path).resolve()
        if not _is_relative_to(full_path, mount_dir):
            raise HTTPException(status_code=403, detail=f"Access denied to path: '{path}'")
        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: '{path}'")
        return full_path

    # Endpoints
    # =========

    @bp.get(
        "",
        summary="Get filesystems information",
        response_model=Sequence[FilesystemDTO],
    )
    async def list_filesystems() -> Sequence[FilesystemDTO]:
        """
        Get the list of filesystems and their mount points.

        Returns:
        - `name`: name of the filesystem: "cfg" or "ws".
        - `mount_dirs`: mapping of the mount point names to their full path in Antares Web Server.
        """

        fs = [FilesystemDTO(name=name, mount_dirs=mount_dirs) for name, mount_dirs in filesystems.items()]
        return fs

    @bp.get(
        "/{fs}",
        summary="Get information of a filesystem",
        response_model=Sequence[MountPointDTO],
    )
    async def list_mount_points(fs: FilesystemName) -> Sequence[MountPointDTO]:
        """
        Get the path and the disk usage of the mount points in a filesystem.

        Args:
        - `fs`: The name of the filesystem: "cfg" or "ws".

        Returns:
        - `name`: name of the mount point.
        - `path`: path of the mount point.
        - `total_bytes`: total size of the mount point in bytes.
        - `used_bytes`: used size of the mount point in bytes.
        - `free_bytes`: free size of the mount point in bytes.
        - `message`: a message describing the status of the mount point.

        Possible error codes:
        - 404 Not Found: If the specified filesystem doesn't exist.
        """

        mount_dirs = _get_mount_dirs(fs)
        tasks = [MountPointDTO.from_path(name, path) for name, path in mount_dirs.items()]
        ws = await asyncio.gather(*tasks)
        return ws

    @bp.get(
        "/{fs}/{mount}",
        summary="Get information of a mount point",
        response_model=MountPointDTO,
    )
    async def get_mount_point(fs: FilesystemName, mount: MountPointName) -> MountPointDTO:
        """
        Get the path and the disk usage of a mount point.

        Args:
        - `fs`: The name of the filesystem: "cfg" or "ws".
        - `mount`: The name of the mount point.

        Returns:
        - `name`: name of the mount point.
        - `path`: path of the mount point.
        - `total_bytes`: total size of the mount point in bytes.
        - `used_bytes`: used size of the mount point in bytes.
        - `free_bytes`: free size of the mount point in bytes.
        - `message`: a message describing the status of the mount point.

        Possible error codes:
        - 404 Not Found: If the specified filesystem or mount point doesn't exist.
        """

        mount_dir = _get_mount_dir(fs, mount)
        return await MountPointDTO.from_path(mount, mount_dir)

    @bp.get(
        "/{fs}/{mount}/ls",
        summary="List files in a mount point",
        response_model=Sequence[FileInfoDTO],
    )
    async def list_files(
        fs: FilesystemName,
        mount: MountPointName,
        path: str = "",
        details: bool = False,
    ) -> Sequence[FileInfoDTO]:
        """
        List files and directories in a mount point.

        Args:
        - `fs`: The name of the filesystem: "cfg" or "ws".
        - `mount`: The name of the mount point.
        - `path`: The relative path of the directory to list.
        - `details`: If true, return the number of files and the total size of each directory.

        > **⚠ Warning:** Using a glob pattern for the `path` parameter (for instance, "**/study.antares")
        > or using the `details` parameter can slow down the response time of this endpoint.

        Returns:
        - `path`: full path of the file or directory in Antares Web Server.
          This path can contain glob patterns (e.g., `*.txt`).
        - `file_type`: file type: "directory", "file", "symlink", "socket", "block_device",
            "character_device", "fifo", or "unknown".
        - `file_count`: number of files of folders in the directory (1 for files).
        - `size_bytes`: size of the file or total size of the directory in bytes.
        - `created`: creation date of the file or directory (local time).
        - `modified`: last modification date of the file or directory (local time).
        - `accessed`: last access date of the file or directory (local time).
        - `message`: a message describing the status of the file.

        Possible error codes:
        - 400 Bad Request: If the specified path is invalid (e.g., contains invalid glob patterns).
        - 404 Not Found: If the specified filesystem or mount point doesn't exist.
        - 403 Forbidden: If the user has no permission to access the directory.
        """

        mount_dir = _get_mount_dir(fs, mount)

        # The following code looks weird, but it's the only way to handle exceptions in generators.
        tasks = []
        iterator = mount_dir.glob(path) if path else mount_dir.iterdir()
        while True:
            try:
                file_path = next(iterator)
            except StopIteration:
                break
            except (OSError, ValueError, IndexError) as exc:
                # Unacceptable pattern: invalid glob pattern or access denied
                raise HTTPException(status_code=400, detail=f"Invalid path: '{path}'. {exc}") from exc
            except NotImplementedError as exc:
                # Unacceptable pattern: non-relative glob pattern
                raise HTTPException(status_code=403, detail=f"Access denied to path: '{path}'. {exc}") from exc
            else:
                file_info = FileInfoDTO.from_path(file_path, details=details)
                tasks.append(file_info)

        file_info_list = await asyncio.gather(*tasks)
        return file_info_list

    @bp.get(
        "/{fs}/{mount}/cat",
        summary="View a text file from a mount point",
        response_class=PlainTextResponse,
        response_description="File content as text",
    )
    async def view_file(
        fs: FilesystemName,
        mount: MountPointName,
        path: str = "",
        encoding: str = "utf-8",
    ) -> str:
        # noinspection SpellCheckingInspection
        """
        View a text file from a mount point.

        Examples:
        ```ini
        [antares]
        version = 820
        caption = default
        created = 1701964773.965127
        lastsave = 1701964773.965131
        author = John DOE
        ```

        Args:
        - `fs`: The name of the filesystem: "cfg" or "ws".
        - `mount`: The name of the mount point.
        - `path`: The relative path of the file to view.
        - `encoding`: The encoding of the file. Defaults to "utf-8".

        Returns:
        - File content as text or binary.

        Possible error codes:
        - 400 Bad Request: If the specified path is missing (empty).
        - 403 Forbidden: If the user has no permission to view the file.
        - 404 Not Found: If the specified filesystem, mount point or file doesn't exist.
        - 417 Expectation Failed: If the specified path is not a text file or if the encoding is invalid.
        """

        mount_dir = _get_mount_dir(fs, mount)
        full_path = _get_full_path(mount_dir, path)

        if full_path.is_dir():
            raise HTTPException(status_code=417, detail=f"Path is not a file: '{path}'")

        elif full_path.is_file():
            try:
                return full_path.read_text(encoding=encoding)
            except LookupError as exc:
                raise HTTPException(status_code=417, detail=f"Unknown encoding: '{encoding}'") from exc
            except UnicodeDecodeError as exc:
                raise HTTPException(status_code=417, detail=f"Failed to decode file: '{path}'") from exc

        else:  # pragma: no cover
            raise HTTPException(status_code=417, detail=f"Unknown file type: '{path}'")

    @bp.get(
        "/{fs}/{mount}/download",
        summary="Download a file from a mount point",
        response_class=StreamingResponse,
        response_description="File content as binary",
    )
    async def download_file(
        fs: FilesystemName,
        mount: MountPointName,
        path: str = "",
    ) -> StreamingResponse:
        """
        Download a file from a mount point.

        > **Note:** Directory download is not supported yet.

        Args:
        - `fs`: The name of the filesystem: "cfg" or "ws".
        - `mount`: The name of the mount point.
        - `path`: The relative path of the file or directory to download.

        Returns:
        - File content as binary.

        Possible error codes:
        - 400 Bad Request: If the specified path is missing (empty).
        - 403 Forbidden: If the user has no permission to download the file.
        - 404 Not Found: If the specified filesystem, mount point or file doesn't exist.
        - 417 Expectation Failed: If the specified path is not a regular file.
        """

        mount_dir = _get_mount_dir(fs, mount)
        full_path = _get_full_path(mount_dir, path)

        if full_path.is_dir():
            raise HTTPException(status_code=417, detail=f"Path is not a file: '{path}'")

        elif full_path.is_file():

            def iter_file() -> Iterator[bytes]:
                with full_path.open(mode="rb") as file:
                    yield from file

            headers = {"Content-Disposition": f"attachment; filename={full_path.name}"}
            return StreamingResponse(iter_file(), media_type="application/octet-stream", headers=headers)

        else:  # pragma: no cover
            raise HTTPException(status_code=417, detail=f"Unknown file type: '{path}'")

    return bp
