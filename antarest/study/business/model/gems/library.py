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

    injection_to_balance: str
    spillage_bound: str
    unsupplied_energy_bound: str


class _GemsThermalCapacityConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    capacity_field: str


class _GemsPortType(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    description: str | None = None
    fields: list[_GemsPortTypeField] = Field(default_factory=list)
    area_connection: _GemsAreaConnection | None = None
    thermal_capacity_connection: _GemsThermalCapacityConnection | None = None


class _GemsModelProperties(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str


class _GemsModels(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    taxonomy_category: str | None = None
    properties: list[_GemsModelProperties] = Field(default_factory=list)

    # These fields are not used in the current implementation
    # That's why they are treated as unknown data
    variables: Any
    binding_constraints: Any
    constraints: Any
    objective_contributions: Any
    extra_outputs: Any
    port_field_definitions: Any


class GemsLibrary(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    description: str | None = None
    version: str | None = None
    port_types: list[_GemsPortType] = Field(alias="port-types", default_factory=list)
    models: list[_GemsModels] = Field(default_factory=list)
