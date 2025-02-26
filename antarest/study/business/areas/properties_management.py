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
from builtins import sorted
from typing import Any, Dict, Iterable, List, Optional, Set, cast

from pydantic import model_validator

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.all_optional_meta import all_optional_model
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


def encode_filter(value: str) -> Set[str]:
    stripped = value.strip()
    return set(re.split(r"\s*,\s*", stripped) if stripped else [])


def decode_filter(encoded_value: Set[str], current_filter: Optional[str] = None) -> str:
    return ", ".join(sort_filter_options(encoded_value))


@all_optional_model
class PropertiesFormFields(FormFieldsBaseModel):
    energy_cost_unsupplied: float
    energy_cost_spilled: float
    non_dispatch_power: bool
    dispatch_hydro_power: bool
    other_dispatch_power: bool
    spread_unsupplied_energy_cost: float
    spread_spilled_energy_cost: float
    filter_synthesis: Set[str]
    filter_by_year: Set[str]
    # version 830
    adequacy_patch_mode: AdequacyPatchMode

    @model_validator(mode="before")
    def validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        filters = {
            "filter_synthesis": values.get("filter_synthesis"),
            "filter_by_year": values.get("filter_by_year"),
        }
        for filter_name, val in filters.items():
            if val is not None:
                options = encode_filter(decode_filter(val))
                if any(opt not in FILTER_OPTIONS for opt in options):
                    raise ValueError(f"Invalid value in '{filter_name}'")

        return values


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
        "encode": encode_filter,
        "decode": decode_filter,
        "default_value": DEFAULT_FILTER_VALUE,
    },
    "filter_by_year": {
        "path": f"{FILTERING_PATH}/filter-year-by-year",
        "encode": encode_filter,
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
    ) -> PropertiesFormFields:
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

            encode = field_info.get("encode") or (lambda x: x)
            return encode(val)

        return PropertiesFormFields.model_construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(
        self,
        study: StudyInterface,
        area_id: str,
        field_values: PropertiesFormFields,
    ) -> None:
        commands: List[UpdateConfig] = []
        file_study = study.get_files()

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]
                decode = info.get("decode")
                target = info["path"].format(area=area_id)
                data = value

                if decode is not None:
                    try:
                        curr_value = file_study.tree.get(target.split("/"))
                    except (ChildNotFoundError, KeyError):
                        curr_value = None
                    data = decode(value, curr_value)

                commands.append(
                    UpdateConfig(
                        target=target,
                        data=data,
                        command_context=self._command_context,
                        study_version=study.version,
                    )
                )

        if commands:
            study.add_commands(commands)
