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
import os
import shutil
import tempfile
import zipfile
from enum import StrEnum
from pathlib import Path
from typing import Any, BinaryIO, Callable, List, Optional, Tuple

import py7zr

from antarest.core.exceptions import BadArchiveContent, ShouldNotHappenException

logger = logging.getLogger(__name__)


class ArchiveFormat(StrEnum):
    ZIP = ".zip"
    SEVEN_ZIP = ".7z"


def is_archive_format(suffix: str) -> bool:
    return suffix in {ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP}


def archive_dir(
    src_dir_path: Path,
    target_archive_path: Path,
    remove_source_dir: bool = False,
    archive_format: Optional[ArchiveFormat] = None,
) -> None:
    if archive_format is not None and target_archive_path.suffix != archive_format:
        raise ShouldNotHappenException(
            f"Non matching archive format {archive_format} and target archive suffix {target_archive_path.suffix}"
        )
    if target_archive_path.suffix == ArchiveFormat.SEVEN_ZIP:
        with py7zr.SevenZipFile(target_archive_path, mode="w") as szf:
            szf.writeall(src_dir_path, arcname="")
    elif target_archive_path.suffix == ArchiveFormat.ZIP:
        with zipfile.ZipFile(target_archive_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=2) as zipf:
            len_dir_path = len(str(src_dir_path))
            for root, _, files in os.walk(src_dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path[len_dir_path:])
    else:
        raise ShouldNotHappenException(f"Unsupported archive format {target_archive_path.suffix}")
    if remove_source_dir:
        shutil.rmtree(src_dir_path)


def unzip(dir_path: Path, zip_path: Path, remove_source_zip: bool = False) -> None:
    with zipfile.ZipFile(zip_path, mode="r") as zipf:
        zipf.extractall(dir_path)
    if remove_source_zip:
        zip_path.unlink()


def is_zip(path: Path) -> bool:
    return path.name.endswith(".zip")


def read_in_zip(
    zip_path: Path,
    inside_zip_path: Path,
    read: Callable[[Optional[Path]], None],
) -> None:
    tmp_dir = None
    try:
        path, tmp_dir = extract_file_to_tmp_dir(zip_path, inside_zip_path)
        read(path)
    except KeyError:
        logger.warning(f"{inside_zip_path} not found in {zip_path}")
        read(None)
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()


def extract_archive(stream: BinaryIO, target_dir: Path) -> None:
    """
    Extract a ZIP archive to a given destination.

    Args:
        stream: The stream containing the archive.
        target_dir: The directory where to extract the archive.

    Raises:
        BadArchiveContent: If the archive is corrupted or in an unknown format.
    """

    # Read the first few bytes to identify the file format
    file_format = stream.read(4)
    stream.seek(0)

    if file_format[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(stream) as zf:
                zf.extractall(path=target_dir)
        except zipfile.BadZipFile as error:
            raise BadArchiveContent("Unsupported ZIP format") from error

    elif file_format[:2] == b"7z":
        try:
            with py7zr.SevenZipFile(stream, "r") as zf:
                zf.extractall(target_dir)
        except py7zr.exceptions.Bad7zFile as error:
            raise BadArchiveContent("Unsupported 7z format") from error

    else:
        raise BadArchiveContent


def extract_file_to_tmp_dir(archive_path: Path, inside_archive_path: Path) -> Tuple[Path, Any]:
    str_inside_archive_path = str(inside_archive_path).replace("\\", "/")
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        if archive_path.suffix == ArchiveFormat.ZIP:
            with zipfile.ZipFile(archive_path) as zip_obj:
                zip_obj.extract(str_inside_archive_path, tmp_dir.name)
        elif archive_path.suffix == ArchiveFormat.SEVEN_ZIP:
            with py7zr.SevenZipFile(archive_path, mode="r") as szf:
                szf.extract(path=tmp_dir.name, targets=[str_inside_archive_path])
        else:
            raise ValueError(f"Unsupported archive format for {archive_path}")
    except Exception as e:
        logger.warning(
            f"Failed to extract {str_inside_archive_path} in archive {archive_path}",
            exc_info=e,
        )
        tmp_dir.cleanup()
        raise
    path = Path(tmp_dir.name) / str_inside_archive_path
    return path, tmp_dir


def read_original_file_in_archive(archive_path: Path, posix_path: str) -> bytes:
    """
    Read a file from an archive.

    Args:
        archive_path: the path to the archive file.
        posix_path: path to the file inside the archive.

    Returns:
        The content of the file as `bytes`.
    """

    if archive_path.suffix == ArchiveFormat.ZIP:
        with zipfile.ZipFile(archive_path) as zip_obj:
            with zip_obj.open(posix_path) as f:
                return f.read()
    elif archive_path.suffix == ArchiveFormat.SEVEN_ZIP:
        with py7zr.SevenZipFile(archive_path, mode="r") as szf:
            output: bytes = szf.read([posix_path])[posix_path].read()
            return output
    else:
        raise ValueError(f"Unsupported {archive_path.suffix} archive format for {archive_path}")


def read_file_from_archive(archive_path: Path, posix_path: str) -> str:
    """
    Read a file from an archive.

    Args:
        archive_path: the path to the archive file.
        posix_path: path to the file inside the archive.

    Returns:
        The content of the file as a string.
    """

    return read_original_file_in_archive(archive_path, posix_path).decode("utf-8")


def extract_lines_from_archive(root: Path, posix_path: str) -> List[str]:
    """
    Extract text lines from various types of files.

    Args:
        root: 7zip or ZIP file containing the study.
        posix_path: Relative path to the file to extract.

    Returns:
        list of lines
    """
    try:
        text = read_file_from_archive(root, posix_path)
        return text.splitlines(keepends=False)
    # File not found in the archive
    except KeyError:
        return []
