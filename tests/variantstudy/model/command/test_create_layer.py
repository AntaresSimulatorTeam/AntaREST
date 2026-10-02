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


from antarest.core.serde.ini_reader import IniReader
from antarest.study.business.model.layer_model import LayerCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestCreateLayer:
    def test_create_layer_success(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        command = CreateLayer(
            parameters=LayerCreation(name="Test Layer1"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )

        output = command.apply(dao)

        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Test Layer1"}

        command = CreateLayer(
            parameters=LayerCreation(name="Test Layer2"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )

        output = command.apply(dao)

        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Test Layer1", "2": "Test Layer2"}

    def test_create_layer_with_explicit_id(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        # Create a layer with an explicit ID
        command = CreateLayer(
            parameters=LayerCreation(name="Test Layer with ID", id="5"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )

        output = command.apply(dao)

        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "5": "Test Layer with ID"}
