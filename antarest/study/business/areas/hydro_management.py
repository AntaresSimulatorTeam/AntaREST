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
import re

from antarest.study.business.model.hydro_management_model import (
    HYDRO_PATH,
    INFLOW_PATH,
    HydroManagementOptions,
    InflowStructure,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_hydro_management import UpdateHydroManagement
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def normalize_key(key: str) -> str:
    return re.sub(r"[\s-]+", "_", key).lower()


class HydroManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_hydro_management_options(self, study: StudyInterface, area_id: str) -> HydroManagementOptions:
        """
        Get management options for a given area
        """
        file_study = study.get_files()
        hydro_config = file_study.tree.get(HYDRO_PATH)

        args = {normalize_key(k): v[area_id] for k, v in hydro_config.items() if area_id in v}

        return HydroManagementOptions.model_validate(args)

    def update_hydro_management_options(
        self,
        study: StudyInterface,
        field_values: HydroManagementOptions,
        area_id: str,
    ) -> None:
        """
        update hydro management options for a given area
        """

        command = UpdateHydroManagement(
            area_id=area_id, properties=field_values, command_context=self._command_context, study_version=study.version
        )

        study.add_commands([command])

    # noinspection SpellCheckingInspection
    def get_inflow_structure(self, study: StudyInterface, area_id: str) -> InflowStructure:
        """
        Retrieves inflow structure values for a specific area within a study.

        Returns:
            InflowStructure: The inflow structure values.
        """
        # NOTE: Focusing on the single field "intermonthly-correlation" due to current model scope.
        path = INFLOW_PATH.format(area_id=area_id)
        file_study = study.get_files()
        inter_monthly_correlation = file_study.tree.get(path.split("/")).get("intermonthly-correlation", 0.5)
        return InflowStructure(inter_monthly_correlation=inter_monthly_correlation)

    # noinspection SpellCheckingInspection
    def update_inflow_structure(self, study: StudyInterface, area_id: str, values: InflowStructure) -> None:
        """
        Updates inflow structure values for a specific area within a study.

        Args:
            study: The study instance to update the inflow data for.
            area_id: The area identifier to update data for.
            values: The new inflow structure values to be updated.

        Raises:
            ValidationError: If the provided `values` parameter is None or invalid.
        """
        # NOTE: Updates only "intermonthly-correlation" due to current model scope.
        path = INFLOW_PATH.format(area_id=area_id)
        command = UpdateConfig(
            target=path,
            data={"intermonthly-correlation": values.inter_monthly_correlation},
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
