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

from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader, YAMLWriter


def test_yaml_reader_and_writer(tmp_path: Path) -> None:
    yaml_file = tmp_path / "test.yaml"
    yaml_dict = {
        "criterion_count_threshold": 1.2,
        "patterns": [{"area": "area1", "criterion": 2.5}, {"area": "area2", "criterion": 3.6}],
        "stopping_threshold": 3.0,
    }
    writer = YAMLWriter()
    # Ensures the writer can create a file that doesn't exist and write the data as it should.
    writer.write(yaml_dict, yaml_file)
    content = yaml_file.read_text()
    assert (
        content
        == """criterion_count_threshold: 1.2
patterns:
- area: area1
  criterion: 2.5
- area: area2
  criterion: 3.6
stopping_threshold: 3.0
"""
    )

    # Ensures the reader can read the data as it should.
    reader = YAMLReader()
    content = reader.read(yaml_file)
    assert content == yaml_dict
    # Also ensures it can read data from a missing file
    empty_content = reader.read(tmp_path / "empty.yaml")
    assert empty_content == {}
