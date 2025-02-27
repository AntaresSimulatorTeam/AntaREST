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

from typing import Any, Dict, List

from pydantic import Field

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

INFLOW_PATH = "input/hydro/prepro/{area_id}/prepro/prepro"
HYDRO_PATH = "input/hydro/hydro"


class InflowStructure(FormFieldsBaseModel):
    """Represents the inflow structure values in the hydraulic configuration."""

    # NOTE: Currently, there is only one field for the inflow structure model
    # due to the scope of hydro config requirements, it may change.
    inter_monthly_correlation: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


@all_optional_model
class HydroManagementOptions(FormFieldsBaseModel):
    inter_daily_breakdown: float = Field(default=1, ge=0)
    intra_daily_modulation: float = Field(default=24, ge=1)
    inter_monthly_breakdown: float = Field(default=1, ge=0)
    reservoir: bool = False
    reservoir_capacity: float = Field(default=0, ge=0)
    follow_load: bool = True
    use_water: bool = False
    hard_bounds: bool = False
    initialize_reservoir_date: int = Field(default=0, ge=0, le=11)
    use_heuristic: bool = True
    power_to_level: bool = False
    use_leeway: bool = False
    leeway_low: float = Field(default=1, ge=0)
    leeway_up: float = Field(default=1, ge=0)
    pumping_efficiency: float = Field(default=1, ge=0)


FIELDS_INFO: Dict[str, FieldInfo] = {
    "inter_daily_breakdown": {
        "path": f"{HYDRO_PATH}/inter-daily-breakdown",
        "default_value": 1,
    },
    "intra_daily_modulation": {
        "path": f"{HYDRO_PATH}/intra-daily-modulation",
        "default_value": 24,
    },
    "inter_monthly_breakdown": {
        "path": f"{HYDRO_PATH}/inter-monthly-breakdown",
        "default_value": 1,
    },
    "reservoir": {"path": f"{HYDRO_PATH}/reservoir", "default_value": False},
    "reservoir_capacity": {
        "path": f"{HYDRO_PATH}/reservoir capacity",
        "default_value": 0,
    },
    "follow_load": {
        "path": f"{HYDRO_PATH}/follow load",
        "default_value": True,
    },
    "use_water": {"path": f"{HYDRO_PATH}/use water", "default_value": False},
    "hard_bounds": {
        "path": f"{HYDRO_PATH}/hard bounds",
        "default_value": False,
    },
    "initialize_reservoir_date": {
        "path": f"{HYDRO_PATH}/initialize reservoir date",
        "default_value": 0,
    },
    "use_heuristic": {
        "path": f"{HYDRO_PATH}/use heuristic",
        "default_value": True,
    },
    "power_to_level": {
        "path": f"{HYDRO_PATH}/power to level",
        "default_value": False,
    },
    "use_leeway": {"path": f"{HYDRO_PATH}/use leeway", "default_value": False},
    "leeway_low": {"path": f"{HYDRO_PATH}/leeway low", "default_value": 1},
    "leeway_up": {"path": f"{HYDRO_PATH}/leeway up", "default_value": 1},
    "pumping_efficiency": {
        "path": f"{HYDRO_PATH}/pumping efficiency",
        "default_value": 1,
    },
}


class HydroManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_hydro_management_options(self, study: StudyInterface, area_id: str) -> HydroManagementOptions:
        """
        Get management options for a given area
        """
        file_study = study.get_files()
        hydro_config = file_study.tree.get(HYDRO_PATH.split("/"))

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            target_name = path.split("/")[-1]
            return hydro_config.get(target_name, {}).get(area_id, field_info["default_value"])

        return HydroManagementOptions.model_construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def update_hydro_management_options(
        self,
        study: StudyInterface,
        field_values: HydroManagementOptions,
        area_id: str,
    ) -> None:
        """
        update hydro management options for a given area
        """
        commands: List[UpdateConfig] = []

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        target="/".join([info["path"], area_id]),
                        data=value,
                        command_context=self._command_context,
                        study_version=study.version,
                    )
                )

        if len(commands) > 0:
            study.add_commands(commands)

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
