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

from antarest.study.business.model.layer_model import LayerCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command.replace_layer_areas import ReplaceLayerAreas
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestReplaceLayerAreas:
    def test_replace_layer_areas_add_success(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        """Test adding areas to a layer."""
        empty_study = empty_study_880

        # Create two areas
        create_area1 = CreateArea(
            area_name="Area1",
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_area1.apply(study_data=empty_study)
        assert output.status

        create_area2 = CreateArea(
            area_name="Area2",
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_area2.apply(study_data=empty_study)
        assert output.status

        # Create a new layer
        create_layer = CreateLayer(
            parameters=LayerCreation(name="Test Layer"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_layer.apply(study_data=empty_study)
        assert output.status

        # Add areas to the layer
        update_command = ReplaceLayerAreas(
            layer_id="1",
            area_ids=["area1", "area2"],
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command.apply(study_data=empty_study)
        assert output.status
        assert "Layer '1' areas replaced" in output.message

        # Verify areas are in the layer
        area1_ui = empty_study.tree.get(["input", "areas", "area1", "ui"])
        assert "1" in area1_ui["layerX"]
        assert "1" in area1_ui["layerY"]
        assert "1" in str(area1_ui["ui"]["layers"])

        area2_ui = empty_study.tree.get(["input", "areas", "area2", "ui"])
        assert "1" in area2_ui["layerX"]
        assert "1" in area2_ui["layerY"]
        assert "1" in str(area2_ui["ui"]["layers"])

    def test_replace_layer_areas_remove_success(
        self, empty_study_880: FileStudy, command_context: CommandContext
    ) -> None:
        """Test removing areas from a layer."""
        empty_study = empty_study_880

        # Create three areas
        for i in range(1, 4):
            create_area = CreateArea(
                area_name=f"Area{i}",
                command_context=command_context,
                study_version=empty_study.config.version,
            )
            output = create_area.apply(study_data=empty_study)
            assert output.status

        # Create a layer
        create_layer = CreateLayer(
            parameters=LayerCreation(name="Test Layer"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_layer.apply(study_data=empty_study)
        assert output.status

        # Add all three areas to the layer
        update_command1 = ReplaceLayerAreas(
            layer_id="1",
            area_ids=["area1", "area2", "area3"],
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command1.apply(study_data=empty_study)
        assert output.status

        # Remove one area from the layer
        update_command2 = ReplaceLayerAreas(
            layer_id="1",
            area_ids=["area1", "area3"],  # area2 removed
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command2.apply(study_data=empty_study)
        assert output.status

        # Verify area1 and area3 are still in the layer
        area1_ui = empty_study.tree.get(["input", "areas", "area1", "ui"])
        assert "1" in area1_ui["layerX"]

        area3_ui = empty_study.tree.get(["input", "areas", "area3", "ui"])
        assert "1" in area3_ui["layerX"]

        # Verify area2 is NOT in the layer
        area2_ui = empty_study.tree.get(["input", "areas", "area2", "ui"])
        assert "1" not in area2_ui["layerX"]
        assert "1" not in area2_ui["layerY"]
        assert "1" not in str(area2_ui["ui"]["layers"])

    def test_replace_layer_areas_layer_not_found(
        self, empty_study_880: FileStudy, command_context: CommandContext
    ) -> None:
        """Test replacing areas in a non-existent layer returns an error."""
        empty_study = empty_study_880

        # Create an area
        create_area = CreateArea(
            area_name="Area1",
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_area.apply(study_data=empty_study)
        assert output.status

        # Try to replace a non-existent layer
        update_command = ReplaceLayerAreas(
            layer_id="999",
            area_ids=["area1"],
            command_context=command_context,
            study_version=empty_study.config.version,
        )

        output = update_command.apply(study_data=empty_study)
        assert not output.status
        assert "Layer is not found" in output.message

    def test_replace_layer_areas_empty_list(self, empty_study_880: FileStudy, command_context: CommandContext) -> None:
        """Test replacing layer with an empty list of areas (removes all areas)."""
        empty_study = empty_study_880

        # Create an area
        create_area = CreateArea(
            area_name="Area1",
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_area.apply(study_data=empty_study)
        assert output.status

        # Create a layer
        create_layer = CreateLayer(
            parameters=LayerCreation(name="Test Layer"),
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = create_layer.apply(study_data=empty_study)
        assert output.status

        # Add area to the layer
        update_command1 = ReplaceLayerAreas(
            layer_id="1",
            area_ids=["area1"],
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command1.apply(study_data=empty_study)
        assert output.status

        # Remove all areas from the layer
        update_command2 = ReplaceLayerAreas(
            layer_id="1",
            area_ids=[],
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = update_command2.apply(study_data=empty_study)
        assert output.status

        # Verify area is NOT in the layer
        area1_ui = empty_study.tree.get(["input", "areas", "area1", "ui"])
        assert "1" not in area1_ui["layerX"]
        assert "1" not in area1_ui["layerY"]
        assert "1" not in str(area1_ui["ui"]["layers"])
