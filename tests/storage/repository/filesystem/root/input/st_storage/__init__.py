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

import pytest

from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.unit_test
def test_get_additional_constraints(
    tmp_path: Path, empty_study_880: FileStudy, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    for file_study in [empty_study_880, empty_study_920]:
        version = file_study.config.version

        # Create 2 areas with both 1 short-term storage
        area_1 = "area1"
        area_2 = "area2"

        CreateArea.model_validate(
            {"area_name": area_1, "command_context": command_context, "study_version": version}
        ).apply(file_study)
        CreateArea.model_validate(
            {"area_name": area_2, "command_context": command_context, "study_version": version}
        ).apply(file_study)

        CreateSTStorage(
            command_context=command_context, area_id=area_1, parameters={"name": "sts1"}, study_version=version
        ).apply(file_study)
        CreateSTStorage(
            command_context=command_context, area_id=area_2, parameters={"name": "sts2"}, study_version=version
        ).apply(file_study)

        # With study 9.2 add additional constraints for one area
        if version == STUDY_VERSION_9_2:
            constraints_path = file_study.config.study_path / "input" / "st-storage" / "constraints" / area_1
            constraints_path.mkdir(parents=True)
            for name in ["additional-constraints.ini", "matrix.txt", "wrong_file.mps"]:
                (constraints_path / name).touch()

        tree = file_study.tree.get(["input", "st-storage"])
        # Ensures we don't see the constraints for v8.8 studies
        if version == STUDY_VERSION_8_8:
            assert list(tree.keys()) == ["clusters", "series"]

        # Ensures we see them for 9.2 study
        else:
            assert list(tree.keys()) == ["clusters", "series", "constraints"]
            constraints = tree["constraints"]
            assert constraints == {
                "area1": {
                    "additional_constraints": "json://additional-constraints.ini",
                    "matrix": "matrixfile://matrix.txt",
                }
            }
