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
from typing import Dict, Mapping

from antarest.core.model import JSON
from antarest.study.business.model.area_properties_model import (
    AreaProperties,
    AreaPropertiesUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_areas_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AreaPropertiesManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_area_properties(self, study: StudyInterface, area_id: str) -> AreaProperties:
        return study.get_study_dao().get_area_properties(area_id)

    def get_all_area_properties(self, study: StudyInterface) -> dict[str, AreaProperties]:
        return study.get_study_dao().get_all_area_properties()

    def update_area_properties(self, study: StudyInterface, area_id: str, properties: AreaPropertiesUpdate) -> None:
        command = UpdateAreasProperties(
            properties={area_id: properties},
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

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
            update_data = update_area.model_dump(exclude_none=True)
            new_areas_by_ids[area_id] = old_area.model_copy(update=update_data)
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
