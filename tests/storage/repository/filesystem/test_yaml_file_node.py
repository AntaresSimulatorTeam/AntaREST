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
import shutil
import textwrap
from pathlib import Path

from antarest.study.model import STUDY_VERSION_8
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLFileNode


def test_get(tmp_path: Path) -> None:
    yaml_path = tmp_path / "file.yml"

    yaml_content = textwrap.dedent(
        """# User comment
criterion_count_threshold: 1.2  # Second user comment
patterns:
- area: area1
  criterion: 2.5
- area: area2
  criterion: 3.6
stopping_threshold: 3.0
"""
    )
    yaml_path.write_text(yaml_content)

    expected_json = {
        "criterion_count_threshold": 1.2,
        "patterns": [{"area": "area1", "criterion": 2.5}, {"area": "area2", "criterion": 3.6}],
        "stopping_threshold": 3.0,
    }
    node = YAMLFileNode(
        config=FileStudyTreeConfig(study_path=yaml_path, path=yaml_path, version=STUDY_VERSION_8, study_id="id"),
    )
    assert node.get() == expected_json
    assert node.get(depth=2) == expected_json

    base_name = str(tmp_path.joinpath("archived"))
    zipped_path = Path(shutil.make_archive(base_name, format="zip", root_dir=tmp_path))

    zipped_node = YAMLFileNode(
        config=FileStudyTreeConfig(
            study_path=tmp_path.joinpath("archived", yaml_path.name),
            path=tmp_path.joinpath("archived", yaml_path.name),
            version=STUDY_VERSION_8,
            study_id="id",
            archive_path=zipped_path,
        ),
    )
    assert zipped_node.get() == expected_json
    assert node.get(depth=2) == expected_json


def test_save(tmp_path: Path) -> None:
    yaml_path = tmp_path / "file.yml"

    node = YAMLFileNode(
        config=FileStudyTreeConfig(study_path=tmp_path, path=yaml_path, version=STUDY_VERSION_8, study_id="id"),
    )

    data = {
        "criterion_count_threshold": 1.2,
        "patterns": [{"area": "area1", "criterion": 2.5}, {"area": "area2", "criterion": 3.6}],
        "stopping_threshold": 3.0,
    }
    node.save(data)
    expected = """criterion_count_threshold: 1.2
patterns:
- area: area1
  criterion: 2.5
- area: area2
  criterion: 3.6
stopping_threshold: 3.0
"""
    assert yaml_path.read_text() == expected
