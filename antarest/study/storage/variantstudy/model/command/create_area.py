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

from typing import Any, Final

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, AreaUI
from antarest.study.business.model.area_properties_model import AdequacyPatchMode, AreaProperties
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationArea
from antarest.study.business.model.hydro_model import HydroManagement, InflowStructure
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_2,
    STUDY_VERSION_10_0,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateArea(ICommand):
    """
    Command used to create a new area in the study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_AREA
    # version 2: remove unused `metadata` field
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    area_name: str

    @model_validator(mode="before")
    @classmethod
    def _validate_metadata(cls, values: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        # Handle version 1 format: {"area_name": "x", "metadata": {...}}
        # The metadata field was never used and is dropped in version 2
        if "metadata" in values:
            values.pop("metadata")
        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        study_data.save_area(self.area_name)
        area_id = transform_name_to_id(self.area_name)
        study_data.save_hydro_management({area_id: HydroManagement()})
        area_properties = AreaProperties()
        if self.study_version >= STUDY_VERSION_8_3:
            area_properties.adequacy_patch_mode = AdequacyPatchMode.OUTSIDE
        study_data.save_area_properties(area_id, area_properties)
        study_data.save_area_ui(area_id, layer=DEFAULT_LAYER_ID, area_ui=AreaUI())

        # Hydro
        allocation = HydroAllocation(allocation=[HydroAllocationArea(area_id=area_id, coefficient=1)])
        correlation = HydroCorrelation(correlation=[HydroCorrelationArea(area_id=area_id, coefficient=100)])
        study_data.save_hydro_allocation({area_id: allocation})
        study_data.save_hydro_correlation({area_id: correlation})
        study_data.save_inflow_structure({area_id: InflowStructure()})
        constants = self.command_context.generator_matrix_constants
        null_matrix = constants.get_null_matrix()
        study_data.save_hydro_energy({area_id: null_matrix})
        study_data.save_hydro_run_of_river({area_id: null_matrix})
        study_data.save_hydro_modulation({area_id: null_matrix})
        study_data.save_hydro_maxpower({area_id: constants.get_hydro_max_power(version=self.study_version)})
        study_data.save_hydro_reservoir({area_id: constants.get_hydro_reservoir(version=self.study_version)})
        if self.study_version > STUDY_VERSION_6_5:
            study_data.save_hydro_credit_modulations({area_id: constants.get_hydro_credit_modulations()})
            study_data.save_hydro_inflow_pattern({area_id: constants.get_hydro_inflow_pattern()})
            study_data.save_hydro_water_values({area_id: null_matrix})
        if self.study_version >= STUDY_VERSION_8_6:
            study_data.save_hydro_mingen({area_id: null_matrix})
        if self.study_version >= STUDY_VERSION_9_2:
            # Read hydro-pmax from generaldata.ini
            compatibility_parameters = study_data.get_compatibility_parameters()
            hydro_pmax = compatibility_parameters.hydro_pmax
            if hydro_pmax == HydroPmax.HOURLY:
                study_data.save_hydro_max_hourly_gen_power({area_id: constants.get_hydro_max_hourly_gen_power()})
                study_data.save_hydro_max_hourly_pump_power({area_id: constants.get_hydro_max_hourly_pump_power()})
                study_data.save_hydro_max_daily_gen_energy({area_id: constants.get_hydro_max_daily_gen_energy()})
                study_data.save_hydro_max_daily_pump_energy({area_id: constants.get_hydro_max_daily_pump_energy()})
        # Matrices
        study_data.save_load({area_id: null_matrix})
        study_data.save_solar({area_id: null_matrix})
        study_data.save_wind({area_id: null_matrix})
        if self.study_version < STUDY_VERSION_10_0:
            study_data.save_reserves({area_id: constants.get_default_reserves()})
        else:
            study_data.save_reserves_global_parameters({area_id: ReservesGlobalParameters()})
        study_data.save_misc_gen({area_id: constants.get_default_miscgen()})

        return command_succeeded(message=f"Area '{self.area_name}' created", result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={"area_name": self.area_name},
            study_version=self.study_version,
            version=self._SERIALIZATION_VERSION,
        )
