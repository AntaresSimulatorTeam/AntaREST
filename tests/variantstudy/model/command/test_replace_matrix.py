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

from unittest.mock import Mock, patch

import numpy as np

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestReplaceMatrix:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        study_path = empty_study.config.study_path
        study_version = empty_study.config.version
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        CreateArea.model_validate(
            {"area_name": area1, "command_context": command_context, "study_version": study_version}
        ).apply(empty_study)

        target_element = f"input/hydro/common/capacity/maxpower_{area1_id}"
        replace_matrix = ReplaceMatrix.model_validate(
            {
                "target": target_element,
                "matrix": [[0]],
                "command_context": command_context,
                "study_version": study_version,
            }
        )
        output = replace_matrix.apply(empty_study)
        assert output.status

        # check the matrices links
        matrix_id = command_context.matrix_service.create([[0]])
        target_path = study_path / f"{target_element}.txt.link"
        assert matrix_id in target_path.read_text()

        target_element = "fake/matrix/path"
        replace_matrix = ReplaceMatrix.model_validate(
            {
                "target": target_element,
                "matrix": [[0]],
                "command_context": command_context,
                "study_version": study_version,
            }
        )
        output = replace_matrix.apply(empty_study)
        assert not output.status
