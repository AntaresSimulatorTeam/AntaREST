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

import pytest

from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_xpansion_constraint import CreateXpansionConstraint
from antarest.study.storage.variantstudy.model.command.create_xpansion_matrix import (
    CreateXpansionCapacity,
    CreateXpansionWeight,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateXpansionResource:
    @staticmethod
    def set_up(empty_study: FileStudy):
        empty_study.tree.save(
            {"user": {"expansion": {"capa": {}, "weights": {}, "constraints": {}, "settings": {}, "candidates": {}}}}
        )

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
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
            output = cmd.apply(study_data=empty_study)
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
            output = cmd.apply(study_data=empty_study)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "weights" / f"{file_name}.link"
            assert resource_path.exists()
            assert resource_path.read_text().startswith("matrix://")
            content = empty_study.tree.get(["user", "expansion", "weights", file_name])
            assert content == {"columns": ["0", "1"], "data": data, "index": ["0", "1"]}

        # Capa
        for file_name in ["capa1.txt", "capa2.txt"]:
            data = [[1, 2], [3, 4]] if file_name == "capa1.txt" else [[5, 6], [7, 8]]
            cmd = CreateXpansionCapacity(
                filename=file_name,
                matrix=data,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_data=empty_study)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "capa" / f"{file_name}.link"
            assert resource_path.exists()
            assert resource_path.read_text().startswith("matrix://")
            content = empty_study.tree.get(["user", "expansion", "capa", file_name])
            assert content == {"columns": ["0", "1"], "data": data, "index": ["0", "1"]}

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_cases(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)

        # Constraints
        file_name = "constraints.ini"
        data = file_name.encode("utf-8")
        CreateXpansionConstraint(
            filename=file_name,
            data=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        ).apply(study_data=empty_study)
        # Tries to re-create the same file
        cmd = CreateXpansionConstraint(
            filename=file_name,
            data=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert f" File '{file_name}' already exists" in output.message

        # Weights
        file_name = "weights.txt"
        data = [[1, 2], [3, 4]]
        CreateXpansionWeight(
            filename=file_name,
            matrix=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        ).apply(study_data=empty_study)
        # Tries to re-create the same file
        cmd = CreateXpansionWeight(
            filename=file_name,
            matrix=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert f" File '{file_name}' already exists" in output.message

        # Capa
        file_name = "constraints.tsv"
        data = [[1, 2], [3, 4]]
        CreateXpansionCapacity(
            filename=file_name,
            matrix=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        ).apply(study_data=empty_study)
        # Tries to re-create the same file
        cmd = CreateXpansionCapacity(
            filename=file_name,
            matrix=data,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert f" File '{file_name}' already exists" in output.message
