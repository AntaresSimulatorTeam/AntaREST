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
import numpy as np
import polars as pl
from polars.testing import assert_frame_equal

from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.model.command.create_xpansion_constraint import CreateXpansionConstraint
from antarest.study.storage.variantstudy.model.command.create_xpansion_matrix import (
    CreateXpansionCapacity,
    CreateXpansionWeight,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestCreateXpansionResource:
    @staticmethod
    def set_up(empty_study: FileStudy) -> None:
        empty_study.tree.save(
            {"user": {"expansion": {"capa": {}, "weights": {}, "constraints": {}, "settings": {}, "candidates": {}}}}
        )

    def test_nominal_case(self, empty_study_870: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_870
        dao = build_dao_from_file_study(empty_study, command_context)
        self.set_up(empty_study)

        # Constraints
        for file_name in ["constraints1.ini", "constraints2.txt"]:
            data = file_name.encode("utf-8")
            cmd = CreateXpansionConstraint(
                filename=file_name,
                data=data,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_dao=dao)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "constraints" / file_name
            assert resource_path.exists()
            assert resource_path.read_text() == file_name

        # Weights
        for file_name in ["weights1.txt", "weights2.txt"]:
            data = [[1, 2], [3, 4]] if file_name == "weights1.txt" else [[5, 6], [7, 8]]
            cmd = CreateXpansionWeight(
                filename=file_name,
                matrix=data,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_dao=dao)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "weights" / f"{file_name}.link"
            assert resource_path.exists()
            assert resource_path.read_text() and not resource_path.read_text().startswith("matrix://")
            matrix_node = empty_study.tree.get_node(["user", "expansion", "weights", file_name])
            assert isinstance(matrix_node, InputSeriesMatrix)
            matrix = matrix_node.parse_as_dataframe()
            expected_matrix = pl.DataFrame(data=np.array(data), schema=["0", "1"])
            assert_frame_equal(matrix, expected_matrix)

        # Capa
        for file_name in ["capa1.txt", "capa2.txt"]:
            data = [[1, 2], [3, 4]] if file_name == "capa1.txt" else [[5, 6], [7, 8]]
            cmd = CreateXpansionCapacity(
                filename=file_name,
                matrix=data,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_dao=dao)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "capa" / f"{file_name}.link"
            assert resource_path.exists()
            assert resource_path.read_text() and not resource_path.read_text().startswith("matrix://")
            matrix_node = empty_study.tree.get_node(["user", "expansion", "capa", file_name])
            assert isinstance(matrix_node, InputSeriesMatrix)
            matrix = matrix_node.parse_as_dataframe()
            expected_matrix = pl.DataFrame(data=np.array(data), schema=["0", "1"])
            assert_frame_equal(matrix, expected_matrix)
