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

    def get_area_properties(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> AreaProperties:
        return study.get_study_dao().get_area_properties(area_id)

    def update_area_properties(
        self,
        study: StudyInterface,
        area_id: str,
        properties: AreaPropertiesUpdate,
    ) -> None:
        command = UpdateAreasProperties(
            properties={area_id: properties},
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
