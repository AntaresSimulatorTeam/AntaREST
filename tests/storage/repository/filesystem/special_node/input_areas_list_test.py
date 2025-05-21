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
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.list import InputAreasList


def test_unarchived(tmp_path: Path):
    file = tmp_path / "list.txt"
    content = """
FR
DE
IT    
"""
    file.write_text(content)

    config = FileStudyTreeConfig(
        study_path=file,
        path=file,
        study_id="id",
        version=-1,
        areas={
            "fr": Area(
                name="FR",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "de": Area(
                name="DE",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "it": Area(
                name="IT",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
    )
    node = InputAreasList(matrix_mapper=Mock(), config=config)

    assert ["FR", "DE", "IT"] == node.get()
    assert not node.check_errors(["FR", "DE", "IT"])

    node.save(["a", "b", "c"])
    assert ["a", "b", "c"] == node.get()
