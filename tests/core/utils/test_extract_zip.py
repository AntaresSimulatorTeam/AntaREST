# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import io
import zipfile
from pathlib import Path

import py7zr
import pytest

from antarest.core.exceptions import BadArchiveContent
from antarest.core.utils.archives import extract_archive


class TestExtractArchive:
    """
    Test the `extract_zip` function.
    """

    def test_extract_zip__with_zip(self, tmp_path: Path):
        # First, create a small ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(zinfo_or_arcname="test.txt", data="Hello world!")

        # Then, call the function
        with open(zip_path, mode="rb") as stream:
            extract_archive(stream, tmp_path)

        # Finally, check the result
        assert (tmp_path / "test.txt").read_text() == "Hello world!"

    def test_extract_zip__with_7z(self, tmp_path: Path):
        # First, create a small ZIP file
        zip_path = tmp_path / "test.7z"
        with py7zr.SevenZipFile(zip_path, mode="w") as zipf:
            zipf.writestr(data="Hello world!", arcname="test.txt")

        # Then, call the function
        with open(zip_path, mode="rb") as stream:
            extract_archive(stream, tmp_path)

        # Finally, check the result
        assert (tmp_path / "test.txt").read_text() == "Hello world!"

    def test_extract_zip__empty_file(self):
        stream = io.BytesIO(b"")

        with pytest.raises(BadArchiveContent):
            extract_archive(stream, Path("dummy/path"))

    def test_extract_zip__corrupted_zip(self):
        stream = io.BytesIO(b"PK\x03\x04 BLURP")

        with pytest.raises(BadArchiveContent):
            extract_archive(stream, Path("dummy/path"))

    def test_extract_zip__corrupted_7z(self):
        stream = io.BytesIO(b"7z BLURP")

        with pytest.raises(BadArchiveContent):
            extract_archive(stream, Path("dummy/path"))

    def test_extract_zip__unknown_format(self):
        stream = io.BytesIO(b"ZORRO")

        with pytest.raises(BadArchiveContent):
            extract_archive(stream, Path("dummy/path"))
