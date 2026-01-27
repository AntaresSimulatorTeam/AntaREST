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

import logging
from typing import Dict, List, Mapping

from antarest.core.exceptions import DuplicateAreaName
from antarest.core.model import JSON
from antarest.study.business.model.area_model import (
    AreaCreation,
    AreaInfo,
    AreaUI,
    AreaUIData,
    AreaUIUpdate,
)
from antarest.study.business.model.area_properties_model import (
    AreaProperties,
    AreaPropertiesUpdate,
    update_area_properties,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.replace_layer_areas import ReplaceLayerAreas
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_areas_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class AreaManager:
    """
    Manages operations related to areas in a study, including retrieval, creation, and updates.
    """

    def __init__(
        self,
        command_context: CommandContext,
    ) -> None:
        """
        Initializes the AreaManager.
        """
        self._command_context = command_context

    def get_all_areas_info(self, study: StudyInterface) -> List[AreaInfo]:
        """Retrieve all physical areas of a raw study."""
        return study.get_study_dao().get_all_areas_info()

    def get_area_ui(self, study: StudyInterface, area_id: str) -> AreaUI:
        """Returns the UI of the layer 0 for a given area"""
        return study.get_study_dao().get_area_ui(area_id)

    def get_all_areas_ui_info(self, study: StudyInterface) -> Dict[str, AreaUIData]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Args:
            study: The raw study object containing the study's data.

        Returns:
            A dictionary mapping area IDs to their UI data.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        return study.get_study_dao().get_all_areas_ui_info()

    def update_layer_areas(self, study: StudyInterface, layer_id: str, areas: List[str]) -> None:
        logger.info(f"Replacing layer {layer_id} areas with {areas}")
        command = ReplaceLayerAreas(
            layer_id=layer_id,
            area_ids=areas,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def create_area(self, study: StudyInterface, area_creation_info: AreaCreation) -> AreaInfo:
        # check if area already exists
        area_id = transform_name_to_id(area_creation_info.name)
        existing_areas = study.get_study_dao().get_all_areas_info()
        existing_area_ids = {area.id for area in existing_areas}
        if area_id in existing_area_ids:
            raise DuplicateAreaName(area_creation_info.name)

        # Create area and apply changes in the study
        command = CreateArea(
            area_name=area_creation_info.name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return AreaInfo(
            id=area_id,
            name=area_creation_info.name,
            # this should always be empty since it's a new area
            thermals=[],
        )

    def update_area_ui(self, study: StudyInterface, area_id: str, area_ui: AreaUIUpdate, layer: str) -> None:
        command = UpdateAreaUI(
            area_id=area_id,
            layer=layer,
            parameters=area_ui,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

    def delete_area(self, study: StudyInterface, area_id: str) -> None:
        command = RemoveArea(
            id=area_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def get_area_properties(self, study: StudyInterface, area_id: str) -> AreaProperties:
        return study.get_study_dao().get_area_properties(area_id)

    def get_all_area_properties(self, study: StudyInterface) -> dict[str, AreaProperties]:
        return study.get_study_dao().get_all_area_properties()

    def update_all_area_properties(
        self, study: StudyInterface, properties: dict[str, AreaPropertiesUpdate]
    ) -> Mapping[str, AreaProperties]:
        """
        Update the properties of ares.

        Args:
            study: The raw study object.
            properties: A mapping of area IDs to area properties.

        Returns:
            A mapping of ALL area IDs to area properties.
        """
        old_areas_by_ids = self.get_all_area_properties(study)
        new_areas_by_ids = dict(old_areas_by_ids)

        areas_properties: Dict[str, AreaPropertiesUpdate] = {}

        for area_id, update_area in properties.items():
            old_area = old_areas_by_ids[area_id]
            new_areas_by_ids[area_id] = update_area_properties(old_area, update_area)
            areas_properties[area_id] = update_area

        command = UpdateAreasProperties(
            properties=areas_properties,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        return new_areas_by_ids

    @staticmethod
    def get_table_schema() -> JSON:
        return AreaProperties.model_json_schema()
