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

from builtins import sorted
from typing import Any, Dict, Iterable, List, Optional, Set, cast

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.model.link_model import comma_separated_enum_list
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel
from antarest.study.model import STUDY_VERSION_8_3
from antarest.study.storage.rawstudy.model.filesystem.config.area import AdequacyPatchMode
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext

AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas/{field}/{{area}}"
OPTIMIZATION_PATH = f"{AREA_PATH}/optimization"
NODAL_OPTIMIZATION_PATH = f"{OPTIMIZATION_PATH}/nodal optimization"
FILTERING_PATH = f"{OPTIMIZATION_PATH}/filtering"
# Keep the order
FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]
DEFAULT_FILTER_VALUE = FILTER_OPTIONS


def sort_filter_options(options: Iterable[str]) -> List[str]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def decode_filter(encoded_value: Set[str], current_filter: Optional[str] = None) -> str:
    return ", ".join(sort_filter_options(encoded_value))


@all_optional_model
class AreaProperties(FormFieldsBaseModel):
    energy_cost_unsupplied: float
    energy_cost_spilled: float
    non_dispatch_power: bool
    dispatch_hydro_power: bool
    other_dispatch_power: bool
    spread_unsupplied_energy_cost: float
    spread_spilled_energy_cost: float
    filter_synthesis: comma_separated_enum_list
    filter_by_year: comma_separated_enum_list
    # version 830
    adequacy_patch_mode: AdequacyPatchMode

    @staticmethod
    def from_files(values: dict[str, Any]) -> "AreaProperties":
        optimization = values["optimization"]["nodal optimization"]
        filtering = values["optimization"]["filtering"]
        args = {
            "energy_cost_unsupplied": values["average_unsupplied_energy_cost"],
            "energy_cost_spilled": values["average_spilled_energy_cost"],
            "non_dispatch_power": optimization["non-dispatchable-power"],
            "dispatch_hydro_power": optimization["dispatchable-hydro-power"],
            "other_dispatch_power": optimization["other-dispatchable-power"],
            "spread_unsupplied_energy_cost": optimization["spread-unsupplied-energy-cost"],
            "spread_spilled_energy_cost": optimization["spread-spilled-energy-cost"],
            "filter_synthesis": filtering["filter-synthesis"],
            "filter_by_year": filtering["filter-year-by-year"],
            "adequacy_patch_mode": values["adequacy_patch"]["adequacy-patch"]["adequacy-patch-mode"],
        }
        return AreaProperties.model_validate(args)

    def optimization_dict(self) -> dict[str, Any]:
        model_dict = self.model_dump(mode="json")
        return {
            "filtering": {
                "filter-synthesis": model_dict["filter_synthesis"],
                "filter-year-by-year": model_dict["filter_by_year"],
            },
            "nodal optimization": {
                "non-dispatchable-power": self.non_dispatch_power,
                "dispatchable-hydro-power": self.dispatch_hydro_power,
                "other-dispatchable-power": self.other_dispatch_power,
                "spread-unsupplied-energy-cost": self.spread_unsupplied_energy_cost,
                "spread-spilled-energy-cost": self.spread_spilled_energy_cost,
            },
        }


FIELDS_INFO: Dict[str, FieldInfo] = {
    "energy_cost_unsupplied": {
        "path": THERMAL_PATH.format(field="unserverdenergycost"),
        "default_value": 0.0,
    },
    "energy_cost_spilled": {
        "path": THERMAL_PATH.format(field="spilledenergycost"),
        "default_value": 0.0,
    },
    "non_dispatch_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/non-dispatchable-power",
        "default_value": True,
    },
    "dispatch_hydro_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/dispatchable-hydro-power",
        "default_value": True,
    },
    "other_dispatch_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/other-dispatchable-power",
        "default_value": True,
    },
    "spread_unsupplied_energy_cost": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/spread-unsupplied-energy-cost",
        "default_value": 0.0,
    },
    "spread_spilled_energy_cost": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/spread-spilled-energy-cost",
        "default_value": 0.0,
    },
    "filter_synthesis": {
        "path": f"{FILTERING_PATH}/filter-synthesis",
        "decode": decode_filter,
        "default_value": DEFAULT_FILTER_VALUE,
    },
    "filter_by_year": {
        "path": f"{FILTERING_PATH}/filter-year-by-year",
        "decode": decode_filter,
        "default_value": DEFAULT_FILTER_VALUE,
    },
    "adequacy_patch_mode": {
        "path": f"{AREA_PATH}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
        "default_value": AdequacyPatchMode.OUTSIDE.value,
        "start_version": STUDY_VERSION_8_3,
    },
}


class PropertiesManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_field_values(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> AreaProperties:
        file_study = study.get_files()
        study_ver = study.version

        def get_value(field_info: FieldInfo) -> Any:
            start_ver = cast(int, field_info.get("start_version", 0))
            end_ver = cast(int, field_info.get("end_version", study_ver))
            is_in_version = start_ver <= study_ver <= end_ver
            if not is_in_version:
                return None

            try:
                val = file_study.tree.get(field_info["path"].format(area=area_id).split("/"))
            except (ChildNotFoundError, KeyError):
                return field_info["default_value"]

            return val

        return AreaProperties.model_validate({name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(
        self,
        study: StudyInterface,
        area_id: str,
        field_values: AreaProperties,
    ) -> None:
        commands: List[UpdateConfig] = []

        modified_fields = field_values.model_dump(mode="json", exclude_none=True)

        for key, value in modified_fields.items():
            target = FIELDS_INFO[key]["path"].format(area=area_id)
            commands.append(
                UpdateConfig(
                    target=target,
                    data=value,
                    command_context=self._command_context,
                    study_version=study.version,
                )
            )

        if commands:
            study.add_commands(commands)
