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

import logging
from typing import Any, Dict, List

from antarest.core.exceptions import DuplicateAreaName
from antarest.study.business.model.area_model import (
    Area,
    AreaCreation,
    AreaUIUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.update_area_ui import UpdateAreaUI
from antarest.study.storage.variantstudy.model.command.update_layer_areas import UpdateLayerAreas
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

    def get_all_areas(self, study: StudyInterface) -> List[Area]:
        """Retrieve all physical areas of a raw study."""
        return study.get_study_dao().get_all_areas()

    def get_all_areas_ui_info(self, study: StudyInterface) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Args:
            study: The raw study object containing the study's data.

        Returns:
            A dictionary containing information about the user interface for the areas.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        return study.get_study_dao().get_all_areas_ui_info()

    def update_layer_areas(self, study: StudyInterface, layer_id: str, areas: List[str]) -> None:
        logger.info(f"Updating layer {layer_id} with areas {areas}")
        command = UpdateLayerAreas(
            layer_id=layer_id,
            area_ids=areas,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def create_area(self, study: StudyInterface, area_creation_info: AreaCreation) -> Area:
        file_study = study.get_files()

        # check if area already exists
        area_id = transform_name_to_id(area_creation_info.name)
        if area_id in set(file_study.config.areas):
            raise DuplicateAreaName(area_creation_info.name)

        # Create area and apply changes in the study
        command = CreateArea(
            area_name=area_creation_info.name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return Area(
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
