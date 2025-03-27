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
    HydroManagement,
    HydroManagementFileData,
    HydroManagementUpdate,
    HydroProperties,
    InflowStructure,
    InflowStructureUpdate,
    get_inflow_path,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_hydro_management import UpdateHydroManagement
from antarest.study.storage.variantstudy.model.command.update_inflow_structure import UpdateInflowStructure
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class HydroManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_all_hydro_properties(self, study: StudyInterface) -> dict[str, HydroProperties]:
        all_hydro_properties = {}

        file_study = study.get_files()
        hydro_management_file_data = HydroManagementFileData(**file_study.tree.get(HYDRO_PATH))

        for area_id in file_study.config.areas:
            hydro_management = hydro_management_file_data.get_hydro_management(area_id)
            inflow_structure = self.get_inflow_structure(study, area_id)
            hydro_properties = HydroProperties(management_options=hydro_management, inflow_structure=inflow_structure)
            all_hydro_properties[area_id] = hydro_properties

        return all_hydro_properties

    def get_hydro_management(self, study: StudyInterface, area_id: str) -> HydroManagement:
        """
        Get management options for a given area
        """
        file_study = study.get_files()

        hydro_properties = HydroManagementFileData(**file_study.tree.get(HYDRO_PATH))

        return hydro_properties.get_hydro_management(area_id, study.version)

    def update_hydro_management(
        self,
        study: StudyInterface,
        properties: HydroManagementUpdate,
        area_id: str,
    ) -> None:
        """
        update hydro management options for a given area
        """

        command = UpdateHydroManagement(
            area_id=area_id, properties=properties, command_context=self._command_context, study_version=study.version
        )

        study.add_commands([command])

    # noinspection SpellCheckingInspection
    def get_inflow_structure(self, study: StudyInterface, area_id: str) -> InflowStructure:
        """
        Retrieves inflow structure values for a specific area within a study.

        Returns:
            InflowStructure: The inflow structure values.
        """

        path = get_inflow_path(area_id)
        file_study = study.get_files()
        inter_monthly_correlation = file_study.tree.get(path).get("intermonthly-correlation", 0.5)
        return InflowStructure(inter_monthly_correlation=inter_monthly_correlation)

    # noinspection SpellCheckingInspection
    def update_inflow_structure(self, study: StudyInterface, area_id: str, properties: InflowStructureUpdate) -> None:
        """
        Updates inflow structure values for a specific area within a study.

        Args:
            study: The study instance to update the inflow data for.
            area_id: The area identifier to update data for.
            properties: The new inflow structure values to be updated.

        Raises:
            ValidationError: If the provided `values` parameter is None or invalid.
        """

        command = UpdateInflowStructure(
            area_id=area_id,
            properties=properties,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
