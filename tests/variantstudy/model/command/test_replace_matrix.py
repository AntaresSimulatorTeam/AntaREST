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

from antarest.core.utils.polars import create_polars_dataframe
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_xpansion_configuration import CreateXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.create_xpansion_matrix import (
    CreateXpansionCapacity,
    CreateXpansionWeight,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestReplaceMatrix:
    def test_apply(self, empty_study_810: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_810
        dao = build_dao_from_file_study(empty_study, command_context)
        study_path = empty_study.config.study_path
        study_version = empty_study.config.version
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        CreateArea.model_validate(
            {"area_name": area1, "command_context": command_context, "study_version": study_version}
        ).apply(dao)

        target_element = f"input/hydro/common/capacity/maxpower_{area1_id}"
        replace_matrix = ReplaceMatrix.model_validate(
            {
                "target": target_element,
                "matrix": [[0]],
                "command_context": command_context,
                "study_version": study_version,
            }
        )
        output = replace_matrix.apply(dao)
        assert output.status

        # check the matrices links
        matrix_id = command_context.matrix_service.create(create_polars_dataframe([[0]]))
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
        output = replace_matrix.apply(dao)
        assert not output.status

    def test_save_xpansion_resource(self, empty_study_810: FileStudy, command_context: CommandContext) -> None:
        study = empty_study_810
        dao = build_dao_from_file_study(study, command_context)
        study_version = study.config.version

        # Create the Xpansion Configuration
        command = CreateXpansionConfiguration(command_context=command_context, study_version=study_version)
        result = command.apply(dao)
        assert result.status

        # Add an xpansion weight
        command = CreateXpansionWeight(
            command_context=command_context,
            study_version=study_version,
            filename="my_file.txt",
            matrix=[[4.1], [3]],
        )
        result = command.apply(dao)
        assert result.status

        # Replace the matrix, it should succeed
        command = ReplaceMatrix(
            command_context=command_context,
            study_version=study_version,
            target="user/expansion/weights/my_file.txt",
            matrix=[[9.1], [4]],
        )
        result = command.apply(dao)
        assert result.status

        # Ensures the data was replaced correctly
        node = study.tree.get_node(["user", "expansion", "weights", "my_file.txt"])
        assert isinstance(node, InputSeriesMatrix)
        matrix = node.parse_as_dataframe().to_numpy().tolist()
        assert matrix == [[9.1], [4.0]]

        # Add an xpansion capacity
        command = CreateXpansionCapacity(
            command_context=command_context,
            study_version=study_version,
            filename="my_capa.txt",
            matrix=[[4.1], [3]],
        )
        result = command.apply(dao)
        assert result.status

        # Replace the matrix, it should succeed
        command = ReplaceMatrix(
            command_context=command_context,
            study_version=study_version,
            target="user/expansion/capa/my_capa.txt",
            matrix=[[9.1], [4]],
        )
        result = command.apply(dao)
        assert result.status

        # Ensures the data was replaced correctly
        node = study.tree.get_node(["user", "expansion", "capa", "my_capa.txt"])
        assert isinstance(node, InputSeriesMatrix)
        matrix = node.parse_as_dataframe().to_numpy().tolist()
        assert matrix == [[9.1], [4.0]]
