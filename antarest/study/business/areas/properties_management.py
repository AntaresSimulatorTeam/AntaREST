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
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set

from pydantic import model_validator

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPatchMode,
    AdequacyPathProperties,
    AreaFolder,
    OptimizationProperties,
    ThermalAreasProperties,
)
from antarest.study.storage.variantstudy.model.command.update_area_properties import UpdateAreasProperties
from antarest.study.storage.variantstudy.model.command_context import CommandContext

AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas"
OPTIMIZATION_PATH = f"{AREA_PATH}/optimization"
ADEQUACY_PATCH_PATH = f"{AREA_PATH}/adequacy_patch"
# Keep the order
FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]


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


class AreaProperties(NamedTuple):
    thermal_properties: Dict[str, Any]
    filtering_props: Dict[str, Any]
    optim_properties: Dict[str, Any]
    adequacy_patch_property: Dict[str, Any]


@all_optional_model
class PropertiesFormFields(FormFieldsBaseModel):
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0
    non_dispatch_power: bool = True
    dispatch_hydro_power: bool = True
    other_dispatch_power: bool = True
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0
    filter_synthesis: Set[str] = set(FILTER_OPTIONS)
    filter_by_year: Set[str] = set(FILTER_OPTIONS)
    # version 830
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE

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

    def to_properties(self) -> AreaProperties:
        thermal_properties = {
            k: v
            for k, v in {
                "unserverdenergycost": self.energy_cost_unsupplied,
                "spilledenergycost": self.energy_cost_spilled,
            }.items()
            if v is not None
        }
        filtering_props = {
            k: v
            for k, v in {"filter-synthesis": self.filter_synthesis, "filter-year-by-year": self.filter_by_year}.items()
            if v is not None
        }
        optim_properties = {
            k: v
            for k, v in {
                "non-dispatchable-power": self.non_dispatch_power,
                "dispatchable-hydro-power": self.dispatch_hydro_power,
                "other-dispatchable-power": self.other_dispatch_power,
                "spread-unsupplied-energy-cost": self.spread_unsupplied_energy_cost,
                "spread-spilled-energy-cost": self.spread_spilled_energy_cost,
            }.items()
            if v is not None
        }
        adequacy_patch_property = {
            k: v
            for k, v in {
                "adequacy-patch-mode": self.adequacy_patch_mode,
            }.items()
            if v is not None
        }

        return AreaProperties(
            thermal_properties=thermal_properties,
            filtering_props=filtering_props,
            optim_properties=optim_properties,
            adequacy_patch_property=adequacy_patch_property,
        )


def update_thermal_properties(
    area_id: str, current_thermal_props: Dict[str, Any], new_thermal_props: Dict[str, Any]
) -> ThermalAreasProperties:
    if unserved_energy_cost := new_thermal_props.get("unserverdenergycost", None):
        current_thermal_props["unserverdenergycost"].update({area_id: unserved_energy_cost})
    if spilled_energy_cost := new_thermal_props.get("spilledenergycost", None):
        current_thermal_props["spilledenergycost"].update({area_id: spilled_energy_cost})

    return ThermalAreasProperties.model_validate(current_thermal_props)


def update_optimization_properties(
    current_optim_properties: Dict[str, Any],
    new_filtering_props: Dict[str, Any],
    new_nodal_props: Dict[str, Any],
) -> OptimizationProperties:
    if filter_synthesis := new_filtering_props.get("filter-synthesis"):
        current_optim_properties["filtering"]["filter-synthesis"] = decode_filter(filter_synthesis)

    if filter_year_by_year := new_filtering_props.get("filter-year-by-year"):
        current_optim_properties["filtering"]["filter-year-by-year"] = decode_filter(filter_year_by_year)

    current_optim_properties["nodal optimization"].update(new_nodal_props)
    return OptimizationProperties.model_validate(current_optim_properties)


def update_adequacy_patch_properties(
    current_adequacy_patch: Dict[str, Any], new_adequacy_patch_prop: Dict[str, Any]
) -> AdequacyPathProperties:
    current_adequacy_patch["adequacy-patch"].update(new_adequacy_patch_prop)
    return AdequacyPathProperties.model_validate(current_adequacy_patch)


class PropertiesManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_field_values(
        self,
        study: StudyInterface,
        area_id: str,
    ) -> PropertiesFormFields:
        file_study = study.get_files()

        current_thermal_props = file_study.tree.get(THERMAL_PATH.split("/"))
        current_optim_properties = file_study.tree.get(OPTIMIZATION_PATH.format(area=area_id).split("/"))
        current_adequacy_patch = file_study.tree.get(ADEQUACY_PATCH_PATH.format(area=area_id).split("/"))

        unserved_energy_cost = current_thermal_props.get("unserverdenergycost", {})
        energy_cost_unsupplied = unserved_energy_cost[area_id] if area_id in unserved_energy_cost else 0.0

        spilled_energy_cost = current_thermal_props.get("spilledenergycost", {})
        energy_cost_spilled = spilled_energy_cost[area_id] if area_id in spilled_energy_cost else 0.0

        args = {
            "energy_cost_unsupplied": energy_cost_unsupplied,
            "energy_cost_spilled": energy_cost_spilled,
            "non_dispatch_power": current_optim_properties["nodal optimization"].get("non-dispatchable-power"),
            "dispatch_hydro_power": current_optim_properties["nodal optimization"].get("dispatchable-hydro-power"),
            "other_dispatch_power": current_optim_properties["nodal optimization"].get("other-dispatchable-power"),
            "spread_unsupplied_energy_cost": current_optim_properties["nodal optimization"].get(
                "spread-unsupplied-energy-cost"
            ),
            "spread_spilled_energy_cost": current_optim_properties["nodal optimization"].get(
                "spread-spilled-energy-cost"
            ),
            "filter_synthesis": encode_filter(current_optim_properties["filtering"].get("filter-synthesis")),
            "filter_by_year": encode_filter(current_optim_properties["filtering"].get("filter-year-by-year")),
            "adequacy_patch_mode": current_adequacy_patch["adequacy-patch"].get("adequacy-patch-mode"),
        }

        return PropertiesFormFields.model_validate(args)

    def set_field_values(
        self,
        study: StudyInterface,
        area_id: str,
        field_values: PropertiesFormFields,
    ) -> None:
        file_study = study.get_files()

        properties = field_values.to_properties()
        new_thermal_props = properties.thermal_properties
        new_filtering_props = properties.filtering_props
        new_nodal_props = properties.optim_properties
        new_adequacy_patch_prop = properties.adequacy_patch_property

        # Update thermal properties
        current_thermal_props = file_study.tree.get(THERMAL_PATH.split("/"))
        thermal_areas_properties = update_thermal_properties(area_id, current_thermal_props, new_thermal_props)

        # Update optimization properties
        current_optim_properties = file_study.tree.get(OPTIMIZATION_PATH.format(area=area_id).split("/"))
        optimization_properties = update_optimization_properties(
            current_optim_properties, new_filtering_props, new_nodal_props
        )

        # Update adequacy patch property
        current_adequacy_patch = file_study.tree.get(ADEQUACY_PATCH_PATH.format(area=area_id).split("/"))
        adequacy_patch_properties = update_adequacy_patch_properties(current_adequacy_patch, new_adequacy_patch_prop)

        command = UpdateAreasProperties(
            areas={area_id: AreaFolder(optimization=optimization_properties, adequacy_patch=adequacy_patch_properties)},
            thermal_properties=[thermal_areas_properties],
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
