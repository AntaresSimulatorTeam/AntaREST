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
#from antarest.study.model import Study
# from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext
# from antarest.study.storage.rawstudy.model.filesystem.config.identifier import LowerCaseIdentifier

INFLOW_PATH = "input/hydro/prepro/{area_id}/prepro/prepro"


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
class ManagementOptionsFormFields(FormFieldsBaseModel):
    inter_daily_breakdown: float = Field(ge=0)
    intra_daily_modulation: float = Field(ge=1)
    inter_monthly_breakdown: float = Field(ge=0)
    reservoir: bool
    reservoir_capacity: float = Field(ge=0)
    follow_load: bool
    use_water: bool
    hard_bounds: bool
    initialize_reservoir_date: int = Field(ge=0, le=11)
    use_heuristic: bool
    power_to_level: bool
    use_leeway: bool
    leeway_low: float = Field(ge=0)
    leeway_up: float = Field(ge=0)
    pumping_efficiency: float = Field(ge=0)


HYDRO_PATH = "input/hydro/hydro"

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
    # def __init__(self, storage_service: StudyStorageService) -> None:
    #    self.storage_service = storage_service
    #    self.area_id = ""

    # @staticmethod
    # def get_id(area_id: str, field_dict: Dict[str, FieldInfo]) -> str:
        """
            Try to match the current area_id with the one from the original file.
            These two ids could mismatch based on their character cases since the id from
            the filesystem could have been modified with capital letters.
            We first convert it into lower case in order to compare both ids.

            Returns the area id from the file if both values matched, the initial area id otherwise.
        """
     #   for file_area_id in field_dict:
     #        if LowerCaseIdentifier.generate_id(file_area_id) == area_id:
     #            return file_area_id
     #    return area_id

    # def get_hydro_config(self, study) -> Dict[str, Dict]:
        """
            Returns a dictionary of hydro configurations
        """
        # file_study = self.storage_service.get_storage(study).get_raw(study)
        # return file_study.tree.get(HYDRO_PATH.split("/"))

    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface, area_id: str) -> ManagementOptionsFormFields:
        """
        Get management options for a given area
        """
        file_study = study.get_files()
        hydro_config = file_study.tree.get(HYDRO_PATH.split("/"))
        #   hydro_config = self.get_hydro_config(study)
        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            target_name = path.split("/")[-1]
            # field_dict = hydro_config.get(target_name, {})
            # return field_dict.get(self.get_id(area_id, field_dict), field_info["default_value"])

            return hydro_config.get(target_name, {}).get(area_id, field_info["default_value"])

        # management_options_data = {name: get_value(info) for name, info in FIELDS_INFO.items()}
        # return ManagementOptionsFormFields.model_construct(**management_options_data)

        return ManagementOptionsFormFields.model_construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self,
        study: StudyInterface,
        field_values: ManagementOptionsFormFields,
        area_id: str,
    ) -> None:
        """
            Set management options for a given area
        """
        commands: List[UpdateConfig] = []

        hydro_config = self.get_hydro_config(study)

        # create a reformatted hydro config dictionary so the fields name can match `FIELDS_INFO` fields name
        reformat_hydro_config = {}
        for key, value in hydro_config.items():
            reformat_hydro_config[key.replace("-", "_").replace(" ", "_")] = value

        for field_name, value in field_values.__iter__():
            if value is not None:
                # retrieve the area id from the original file, including its capital letters
                file_area_id = self.get_id(area_id, reformat_hydro_config.get(field_name, {}))
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        # target="/".join([info["path"], file_area_id]), # update the right fields
                        target="/".join([info["path"], area_id]),
                        data=value,
                        command_context=self._command_context,
                        # command_context=self.storage_service.variant_study_service.command_factory.command_context,
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
