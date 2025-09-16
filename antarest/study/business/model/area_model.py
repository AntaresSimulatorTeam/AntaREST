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

import enum
from typing import Any, Dict, List, Mapping, Optional, Sequence

from pydantic import Field, field_validator

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.model.area_properties_model import (
    AreaProperties,
    AreaPropertiesUpdate,
    decode_filter,
    encode_filter,
)
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPatchMode,
    AdequacyPathFileData,
    AreaFileData,
    OptimizationFileData,
)
from antarest.study.storage.rawstudy.model.filesystem.config.validation import validate_filtering


class AreaType(enum.Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class Area(AntaresBaseModel):
    id: str
    name: str
    type: AreaType
    set: Optional[List[str]] = None
    thermals: Optional[List[ThermalCluster]] = None


class AreaCreation(AntaresBaseModel):
    name: str
    type: AreaType
    set: Optional[List[str]] = None


class UpdateAreaUi(AntaresBaseModel, extra="forbid", populate_by_name=True):
    x: int = Field(title="X position")
    y: int = Field(title="Y position")
    color_rgb: Sequence[int] = Field(title="RGB color", alias="colorRgb")
    layer_x: Mapping[int, int] = Field(default_factory=dict, title="X position of each layer", alias="layerX")
    layer_y: Mapping[int, int] = Field(default_factory=dict, title="Y position of each layer", alias="layerY")
    layer_color: Mapping[int, str] = Field(default_factory=dict, title="Color of each layer", alias="layerColor")


# noinspection SpellCheckingInspection
@all_optional_model
@camel_case_model
class AreaOutput(
    AntaresBaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    DTO object use to get the area information using a flat structure.
    """

    average_unsupplied_energy_cost: float = Field(0.0, description="average unserverd energy cost (€/MWh)")
    average_spilled_energy_cost: float = Field(0.0, description="average spilled energy cost (€/MWh)")
    filter_synthesis: str = Field("")
    filter_year_by_year: str = Field("")
    non_dispatchable_power: bool = Field(default=True)
    dispatchable_hydro_power: bool = Field(default=True)
    other_dispatchable_power: bool = Field(default=True)
    spread_unsupplied_energy_cost: float = Field(default=0.0)
    spread_spilled_energy_cost: float = Field(default=0.0)
    adequacy_patch_mode: Optional[AdequacyPatchMode] = Field(default=None)

    @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
    def _validate_filtering(cls, v: Any) -> str:
        return validate_filtering(v)

    @classmethod
    def from_model(
        cls,
        area_folder: AreaFileData,
        *,
        average_unsupplied_energy_cost: float,
        average_spilled_energy_cost: float,
    ) -> "AreaOutput":
        """
        Creates a `GetAreaDTO` object from configuration data.

        Args:
            area_folder: Configuration data read from the `/input/areas/<area>` information.
            average_unsupplied_energy_cost: Unserverd energy cost (€/MWh).
            average_spilled_energy_cost: Spilled energy cost (€/MWh).
        Returns:
            The `GetAreaDTO` object.
        """
        nodal_opt = area_folder.optimization.nodal_optimization
        filtering = area_folder.optimization.filtering
        adequacy_section = area_folder.adequacy_patch.adequacy_patch if area_folder.adequacy_patch else None

        properties = AreaProperties(
            energy_cost_unsupplied=average_unsupplied_energy_cost,
            energy_cost_spilled=average_spilled_energy_cost,
            non_dispatch_power=nodal_opt.non_dispatchable_power,
            dispatch_hydro_power=nodal_opt.dispatchable_hydro_power,
            other_dispatch_power=nodal_opt.other_dispatchable_power,
            spread_unsupplied_energy_cost=nodal_opt.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=nodal_opt.spread_spilled_energy_cost,
            filter_synthesis=encode_filter(filtering.filter_synthesis),
            filter_by_year=encode_filter(filtering.filter_year_by_year),
            adequacy_patch_mode=(
                adequacy_section.adequacy_patch_mode if adequacy_section else AdequacyPatchMode.OUTSIDE
            ),
        )
        area_output = cls.from_properties(properties)
        if adequacy_section is None:
            area_output.adequacy_patch_mode = None
        return area_output

    @classmethod
    def from_properties(cls, properties: AreaProperties) -> "AreaOutput":
        return cls(
            average_unsupplied_energy_cost=properties.energy_cost_unsupplied,
            average_spilled_energy_cost=properties.energy_cost_spilled,
            filter_synthesis=decode_filter(properties.filter_synthesis),
            filter_year_by_year=decode_filter(properties.filter_by_year),
            non_dispatchable_power=properties.non_dispatch_power,
            dispatchable_hydro_power=properties.dispatch_hydro_power,
            other_dispatchable_power=properties.other_dispatch_power,
            spread_unsupplied_energy_cost=properties.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=properties.spread_spilled_energy_cost,
            adequacy_patch_mode=properties.adequacy_patch_mode,
        )

    def to_properties(self) -> AreaProperties:
        data: Dict[str, Any] = {}
        if self.average_unsupplied_energy_cost is not None:
            data["energy_cost_unsupplied"] = self.average_unsupplied_energy_cost
        if self.average_spilled_energy_cost is not None:
            data["energy_cost_spilled"] = self.average_spilled_energy_cost
        if self.non_dispatchable_power is not None:
            data["non_dispatch_power"] = self.non_dispatchable_power
        if self.dispatchable_hydro_power is not None:
            data["dispatch_hydro_power"] = self.dispatchable_hydro_power
        if self.other_dispatchable_power is not None:
            data["other_dispatch_power"] = self.other_dispatchable_power
        if self.spread_unsupplied_energy_cost is not None:
            data["spread_unsupplied_energy_cost"] = self.spread_unsupplied_energy_cost
        if self.spread_spilled_energy_cost is not None:
            data["spread_spilled_energy_cost"] = self.spread_spilled_energy_cost
        if self.filter_synthesis is not None:
            data["filter_synthesis"] = encode_filter(self.filter_synthesis)
        if self.filter_year_by_year is not None:
            data["filter_by_year"] = encode_filter(self.filter_year_by_year)
        if self.adequacy_patch_mode is not None:
            data["adequacy_patch_mode"] = self.adequacy_patch_mode
        return AreaProperties(**data)

    def to_properties_update(self) -> AreaPropertiesUpdate:
        payload = self.model_dump(exclude_none=True, exclude_unset=True, by_alias=True)
        return AreaPropertiesUpdate(**payload)

    def _to_optimization(self) -> OptimizationFileData:
        obj = {name: getattr(self, name) for name in OptimizationFileData.FilteringSection.model_fields}
        filtering_section = OptimizationFileData.FilteringSection(**obj)
        obj = {name: getattr(self, name) for name in OptimizationFileData.ModalOptimizationSection.model_fields}
        nodal_optimization_section = OptimizationFileData.ModalOptimizationSection(**obj)
        args = {"filtering": filtering_section, "nodal_optimization": nodal_optimization_section}
        return OptimizationFileData.model_validate(args)

    def _to_adequacy_patch(self) -> Optional[AdequacyPathFileData]:
        obj = {name: getattr(self, name) for name in AdequacyPathFileData.AdequacyPathSection.model_fields}
        # If all fields are `None`, the object is empty.
        if all(value is None for value in obj.values()):
            return None
        adequacy_path_section = AdequacyPathFileData.AdequacyPathSection(**obj)
        return AdequacyPathFileData.model_validate({"adequacy_patch": adequacy_path_section})
