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

from typing import Any, Dict, Set

from antarest.study.business.model.area_properties_model import AreaProperties, AreaPropertiesProperties, decode_filter, \
    AreaPropertiesUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.area import ThermalAreasProperties, AreaFolder, \
    OptimizationProperties, AdequacyPathProperties
from antarest.study.storage.variantstudy.model.command.update_area_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext


THERMAL_PATH = ["input", "thermal", "areas"]
OPTIMIZATION_PATH = ["input", "areas", "{area_id}", "optimization"]
ADEQUACY_PATCH_PATH = ["input", "areas", "{area_id}", "adequacy_patch"]


class AreaPropertiesManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_area_properties(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> AreaProperties:
        file_study = study.get_files()

        current_thermal_props = file_study.tree.get(THERMAL_PATH)
        current_optim_properties = file_study.tree.get([s.format(area_id=area_id) for s in OPTIMIZATION_PATH])
        current_adequacy_patch = file_study.tree.get([s.format(area_id=area_id) for s in ADEQUACY_PATCH_PATH])

        properties = {
            **current_thermal_props,
            **current_optim_properties.get("nodal optimization", {}),
            **current_optim_properties.get("filtering", {}),
            **current_adequacy_patch
        }

        ThermalAreasProperties(**current_thermal_props)
        OptimizationProperties(**current_optim_properties)
        AdequacyPathProperties(**current_adequacy_patch)

        area_properties = AreaPropertiesProperties.model_validate(properties)

        return AreaProperties.model_validate(area_properties.get_area_properties(area_id))

    def update_area_properties(
        self,
        study: StudyInterface,
        area_id: str,
        area_properties: AreaPropertiesUpdate,
    ) -> None:

        command = UpdateAreasProperties(
            areas_properties={area_id: area_properties},
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
