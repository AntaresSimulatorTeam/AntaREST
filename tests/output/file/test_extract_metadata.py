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
import zipfile
from pathlib import Path

import pytest

from antarest.output.filestudy.extract_metadata import extract_metadata


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    target = tmp_path / "STA-mini"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(target)
    return target / "STA-mini" / "output" / "20201014-1427eco"


def test_extract_output_metadata(output_path: Path):
    metadata = extract_metadata(output_path)
    assert metadata.name == "20201014-1427eco"
    assert metadata.mode == "Economy"
    assert not metadata.archived
    assert metadata.nb_years == 1
    assert not metadata.by_year
    assert metadata.synthesis
