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
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel


class GemsPortTypeField(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str


class GemsPortType(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    description: str | None = None
    fields: list[GemsPortTypeField] = Field(default_factory=list)


class GemsModels(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class GemsLibrary(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    description: str | None = None
    version: str | None = None
    port_types: list[GemsPortTypeField] = Field(alias="port-types", default_factory=list)
    models: list[GemsModels] = Field(default_factory=list)
