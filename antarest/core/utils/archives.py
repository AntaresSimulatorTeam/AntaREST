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
import functools
import logging
import os
import shutil
import tempfile
import zipfile
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, BinaryIO

import py7zr

from antarest.core.exceptions import BadArchiveContent, ShouldNotHappenException

logger = logging.getLogger(__name__)


@functools.cache
def _has_7z() -> bool:
    return shutil.which("7z") is not None


class ArchiveFormat(StrEnum):
    ZIP = ".zip"
    SEVEN_ZIP = ".7z"


def is_archive_format(suffix: str) -> bool:
    return suffix in {ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP}


def archive_dir(
    src_dir_path: Path,
    target_archive_path: Path,
    remove_source_dir: bool = False,
    archive_format: ArchiveFormat | None = None,
) -> None:
    if archive_format is not None and target_archive_path.suffix != archive_format:
        raise ShouldNotHappenException(
            f"Non matching archive format {archive_format} and target archive suffix {target_archive_path.suffix}"
        )
    if target_archive_path.suffix == ArchiveFormat.SEVEN_ZIP:
        # if 7z is available on the machine, uses it
        if _has_7z():
            logger.info("Using 7z to create archive")
            target_archive_path.unlink(missing_ok=True)
            try:
                run(["7z", "a", str(target_archive_path.resolve()), "."], cwd=str(src_dir_path), check=True)
            except CalledProcessError as e:
                logger.error(f"Error while creating archive: {e}")
                raise
        # else, fallback to py7zr, less performant
        else:
            logger.info("Using py7zr to create archive")
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


def extract_archive_from_path(archive_path: Path, target_dir: Path) -> None:
    """
    Extract an archive from a file path, using the native 7z CLI when available.

    Args:
        archive_path: Path to the archive file (.7z or .zip).
        target_dir: Directory where the archive contents will be extracted.

    Raises:
        BadArchiveContent: If the archive format is unsupported or extraction fails.
    """
    suffix = archive_path.suffix.lower()
    if suffix not in {ArchiveFormat.SEVEN_ZIP, ArchiveFormat.ZIP}:
        raise BadArchiveContent(f"Unsupported archive format: {suffix}")

    if _has_7z():
        logger.info("Using 7z CLI to extract archive %s", archive_path)
        try:
            run(["7z", "x", str(archive_path), f"-o{target_dir}", "-y"], check=True)
        except CalledProcessError as e:
            raise BadArchiveContent(f"7z extraction failed for {archive_path}") from e
    else:
        if suffix == ArchiveFormat.SEVEN_ZIP:
            logger.info("Using py7zr to extract archive %s", archive_path)
            try:
                with py7zr.SevenZipFile(archive_path, "r") as szf:
                    szf.extractall(target_dir)
            except py7zr.exceptions.Bad7zFile as e:
                raise BadArchiveContent("Unsupported 7z format") from e
        else:
            logger.info("Using zipfile to extract archive %s", archive_path)
            try:
                with zipfile.ZipFile(archive_path, mode="r") as zf:
                    zf.extractall(target_dir)
            except zipfile.BadZipFile as e:
                raise BadArchiveContent("Unsupported ZIP format") from e


def unzip(dir_path: Path, zip_path: Path) -> None:
    """Extract an archive to ``dir_path`` and delete the archive file afterwards."""
    extract_archive_from_path(zip_path, dir_path)
    zip_path.unlink()


def is_zip(path: Path) -> bool:
    return path.name.endswith(".zip")


def read_in_zip(
    zip_path: Path,
    inside_zip_path: Path,
    read: Callable[[Path | None], None],
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


def extract_archive_from_stream(stream: BinaryIO, target_dir: Path, tmp_dir: Path | None = None) -> None:
    """
    Extract an archive from a stream to a given destination.

    ZIP archives are extracted directly from the stream.
    7z archives are written to a temporary file first, then extracted
    using ``extract_archive_from_path`` (which uses native 7z CLI when available).

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
            with zipfile.ZipFile(stream, mode="r") as zf:
                zf.extractall(target_dir)
        except zipfile.BadZipFile as e:
            raise BadArchiveContent("Unsupported ZIP format") from e
    elif file_format[:2] == b"7z":
        with tempfile.NamedTemporaryFile(suffix=ArchiveFormat.SEVEN_ZIP, delete=False, dir=tmp_dir) as tmp:
            tmp_path = Path(tmp.name)
            shutil.copyfileobj(stream, tmp)
        try:
            extract_archive_from_path(tmp_path, target_dir)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        raise BadArchiveContent


def extract_file_to_tmp_dir(archive_path: Path, inside_archive_path: Path) -> tuple[Path, Any]:
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


def extract_lines_from_archive(root: Path, posix_path: str) -> list[str]:
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
