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

from antarest.core.utils.files import temp_file_path


def test_temp_path_creation_does_not_create_file(tmp_path: Path) -> None:
    tmp_dir = tmp_path
    with temp_file_path(tmp_dir) as tmp_file:
        assert tmp_file.parent == tmp_dir
        assert not tmp_file.exists()


def test_temp_file_is_removed_on_exit(tmp_path: Path) -> None:
    tmp_dir = tmp_path

    with temp_file_path(tmp_dir) as tmp_file:
        assert not tmp_file.exists()
        tmp_file.touch()
        assert tmp_file.exists()

    assert not tmp_file.exists()
