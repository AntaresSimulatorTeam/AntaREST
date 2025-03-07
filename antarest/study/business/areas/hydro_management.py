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

from antarest.study.business.model.hydro_model import (
    HYDRO_PATH,
    HydroProperties,
    HydroPropertiesInternal,
    get_hydro_id,
)
from antarest.study.business.model.inflow_model import INFLOW_PATH, InflowProperties
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_hydro_management import UpdateHydroProperties
from antarest.study.storage.variantstudy.model.command.update_inflow_properties import UpdateInflowProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class HydroManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_hydro_properties(self, study: StudyInterface, area_id: str) -> HydroProperties:
        """
        Get management options for a given area
        """
        file_study = study.get_files()
        hydro_config = file_study.tree.get(HYDRO_PATH)

        new_area_id = get_hydro_id(area_id, hydro_config)
        args = {k: v[new_area_id] for k, v in hydro_config.items() if new_area_id in v}

        validated_args = HydroPropertiesInternal.model_validate(args).model_dump()

        return HydroProperties(**validated_args)

    def update_hydro_properties(
        self,
        study: StudyInterface,
        properties: HydroProperties,
        area_id: str,
    ) -> None:
        """
        update hydro management options for a given area
        """

        command = UpdateHydroProperties(
            area_id=area_id, properties=properties, command_context=self._command_context, study_version=study.version
        )

        study.add_commands([command])

    # noinspection SpellCheckingInspection
    def get_inflow_properties(self, study: StudyInterface, area_id: str) -> InflowProperties:
        """
        Retrieves inflow structure values for a specific area within a study.

        Returns:
            InflowStructure: The inflow structure values.
        """

        path = [s.format(area_id=area_id) for s in INFLOW_PATH]
        file_study = study.get_files()
        inter_monthly_correlation = file_study.tree.get(path).get("intermonthly-correlation", 0.5)
        return InflowProperties(inter_monthly_correlation=inter_monthly_correlation)

    # noinspection SpellCheckingInspection
    def update_inflow_properties(self, study: StudyInterface, area_id: str, properties: InflowProperties) -> None:
        """
        Updates inflow structure values for a specific area within a study.

        Args:
            study: The study instance to update the inflow data for.
            area_id: The area identifier to update data for.
            properties: The new inflow structure values to be updated.

        Raises:
            ValidationError: If the provided `values` parameter is None or invalid.
        """

        command = UpdateInflowProperties(
            area_id=area_id,
            properties=properties,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
