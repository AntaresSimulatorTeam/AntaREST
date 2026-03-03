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
from pathlib import Path

import pytest

from antarest.lfs.dir_lfs import DirLargeFileStorage


def test_lfs(tmp_path: Path):
    storage = DirLargeFileStorage(tmp_path / "lfs")

    assert not storage.file_exists("unknown")

    src_file_path = tmp_path / "input.txt"
    src_file_path.write_bytes("My content".encode("utf-8"))
    storage.write_file("my-blob", src_file_path)

    assert storage.file_exists("my-blob")

    target_path = tmp_path / "output.txt"
    storage.read_file("my-blob", target_path)
    assert target_path.read_bytes().decode("utf-8") == "My content"

    storage.delete_file("my-blob")
    assert not storage.file_exists("my-blob")

    target_path = tmp_path / "output-2.txt"
    with pytest.raises(FileNotFoundError):
        storage.read_file("my-blob", target_path)
