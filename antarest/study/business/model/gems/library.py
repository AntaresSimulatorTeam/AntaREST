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
from typing import Any

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class _GemsPortTypeField(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str


class _GemsAreaConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    injection_to_balance: str | None = None
    spillage_bound: str | None = None
    unsupplied_energy_bound: str | None = None


class _GemsThermalCapacityConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    capacity_field: str


class _GemsPortType(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    fields: list[_GemsPortTypeField] = Field(default_factory=list)
    area_connection: _GemsAreaConnection | None = None
    thermal_capacity_connection: _GemsThermalCapacityConnection | None = None


class _GemsModelsProperties(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str


class _GemsModelsParameters(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    time_dependent: bool
    scenario_dependent: bool


class _GemsModelsPorts(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    type: str


class _GemsModels(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    taxonomy_category: str | None = None
    properties: list[_GemsModelsProperties] = Field(default_factory=list)
    parameters: list[_GemsModelsParameters] = Field(default_factory=list)
    ports: list[_GemsModelsPorts] = Field(default_factory=list)

    # These fields are not used in the current implementation
    # That's why they are treated as unknown data
    variables: Any | None = None
    binding_constraints: Any | None = None
    constraints: Any | None = None
    objective_contributions: Any | None = None
    extra_outputs: Any | None = None
    port_field_definitions: Any | None = None


class GemsLibrary(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    version: str | None = None
    port_types: list[_GemsPortType] = Field(default_factory=list)
    models: list[_GemsModels] = Field(default_factory=list)
