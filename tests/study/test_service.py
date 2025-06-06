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
from pathlib import Path
from unittest.mock import patch

import pytest

from antarest.study.service import get_disk_usage


def test_get_disk_usage__nominal_case(tmp_path: Path) -> None:
    """
    This test ensures that the 'get_disk_usage' function handles a typical directory structure correctly.
    """
    tmp_path.joinpath("input").mkdir()
    ini_data = b"[config]\nkey = value"
    tmp_path.joinpath("input/params.ini").write_bytes(ini_data)
    tmp_path.joinpath("input/series").mkdir()
    series_data = b"10\n20\n"
    tmp_path.joinpath("input/series/data.tsv").write_bytes(series_data)
    assert get_disk_usage(tmp_path) == len(ini_data) + len(series_data)


@pytest.mark.parametrize("suffix", [".zip", ".7z", ".ZIP"])
def test_get_disk__usage_archive(tmp_path: Path, suffix: str) -> None:
    """
    This test ensures that the 'get_disk_usage' function correctly handles archive files (.zip, .7z).
    """
    compressed_path = tmp_path.joinpath("study").with_suffix(suffix)
    compressed_data = b"dummy archive content"
    compressed_path.write_bytes(compressed_data)
    assert get_disk_usage(tmp_path) == len(compressed_data)


def test_gest_disk_usage__unknown_format(tmp_path: Path) -> None:
    """
    This test ensures that the 'get_disk_usage' function handles unknown directory formats appropriately.
    """
    path = tmp_path.joinpath("study.dat")
    path.touch()
    with pytest.raises(NotADirectoryError):
        get_disk_usage(path)


def test_gest_disk_usage_exceptions(tmp_path: Path) -> None:
    """
    This test ensures that the 'get_disk_usage' function handles exceptions appropriately.
    """
    for folder in ["study", "study2"]:
        (tmp_path / folder).mkdir()
        file_path = tmp_path / folder / "file.txt"
        file_path.write_bytes(b"10")

    with patch("os.scandir", side_effect=FileNotFoundError("File doesn't exist")):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 0

    with patch("os.DirEntry.is_file", side_effect=FileNotFoundError("File doesn't exist")):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 0

    with patch("os.DirEntry.stat", side_effect=FileNotFoundError("File doesn't exist")):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 0

    with patch("os.DirEntry.is_dir", side_effect=FileNotFoundError("File doesn't exist")):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 0

    with patch("os.scandir", side_effect=PermissionError("Access denied")):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 0

    # Mocks the case where the first file raises an exception. We should see the second file size in the result
    with patch("os.DirEntry.is_file", side_effect=[False, FileNotFoundError("File doesn't exist"), False, True]):
        disk_usage = get_disk_usage(tmp_path)
        assert disk_usage == 2
