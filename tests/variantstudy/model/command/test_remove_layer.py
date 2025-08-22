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

from antarest.core.serde.ini_reader import IniReader
from antarest.study.business.model.layer_model import Layer, LayerCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command.remove_layer import RemoveLayer
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestRemoveLayer:
    @pytest.mark.unit_test
    def test_remove_layer_success(self, empty_study_880: FileStudy, command_context: CommandContext):
        empty_study = empty_study_880

        create_command1 = CreateLayer(
            parameters=LayerCreation(name="Test Layer1"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_command1.apply(study_data=empty_study)
        assert output.status

        create_command2 = CreateLayer(
            parameters=LayerCreation(name="Test Layer2"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_command2.apply(study_data=empty_study)
        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Test Layer1", "2": "Test Layer2"}

        remove_command = RemoveLayer(
            parameters=Layer(id="1"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = remove_command.apply(study_data=empty_study)
        assert output.status
        assert "Layer 1 deleted successfully." in output.message

        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "2": "Test Layer2"}

        remove_command2 = RemoveLayer(
            parameters=Layer(id="2"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = remove_command2.apply(study_data=empty_study)
        assert output.status
        assert "Layer 2 deleted successfully." in output.message

        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All"}

    @pytest.mark.unit_test
    def test_remove_layer_not_found(self, empty_study_880: FileStudy, command_context: CommandContext):
        empty_study = empty_study_880

        remove_command = RemoveLayer(
            parameters=Layer(id="999"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = remove_command.apply(study_data=empty_study)

        assert not output.status

    @pytest.mark.unit_test
    def test_remove_layer_zero_not_allowed(self, empty_study_880: FileStudy, command_context: CommandContext):
        empty_study = empty_study_880

        remove_command = RemoveLayer(
            parameters=Layer(id="0"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = remove_command.apply(study_data=empty_study)

        assert not output.status
