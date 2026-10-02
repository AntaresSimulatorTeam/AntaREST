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
from antarest.study.business.model.layer_model import LayerCreation, LayerUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command.update_layer import UpdateLayer
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


class TestUpdateLayerName:
    def test_update_layer_name_success(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        create_command = CreateLayer(
            parameters=LayerCreation(name="Original Layer Name"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_command.apply(study_dao=dao)
        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Original Layer Name"}

        update_command = UpdateLayer(
            parameters=LayerUpdate(id="1", name="Updated Layer Name"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command.apply(study_dao=dao)
        assert output.status
        assert "Updated Layer Name" in output.message

        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Updated Layer Name"}

    def test_update_multiple_layers_names(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        create_command1 = CreateLayer(
            parameters=LayerCreation(name="Layer One"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_command1.apply(study_dao=dao)
        assert output.status

        create_command2 = CreateLayer(
            parameters=LayerCreation(name="Layer Two"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_command2.apply(study_dao=dao)
        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Layer One", "2": "Layer Two"}

        update_command1 = UpdateLayer(
            parameters=LayerUpdate(id="1", name="Modified Layer One"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command1.apply(study_dao=dao)
        assert output.status

        update_command2 = UpdateLayer(
            parameters=LayerUpdate(id="2", name="Modified Layer Two"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command2.apply(study_dao=dao)
        assert output.status

        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers == {"0": "All", "1": "Modified Layer One", "2": "Modified Layer Two"}

    def test_update_layer_not_found(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        update_command = UpdateLayer(
            parameters=LayerUpdate(id="999", name="Non-existent Layer"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command.apply(study_dao=dao)

        assert not output.status

    def test_update_layer_zero_name(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_880
        dao = build_dao_from_file_study(empty_study, command_context)

        update_command = UpdateLayer(
            parameters=LayerUpdate(id="0", name="All Areas Updated"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command.apply(study_dao=dao)
        assert output.status

        link = IniReader()
        layers = link.read(empty_study.config.study_path / "layers/layers.ini")["layers"]
        assert layers["0"] == "All Areas Updated"
