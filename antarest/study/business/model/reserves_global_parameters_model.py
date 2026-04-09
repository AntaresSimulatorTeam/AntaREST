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
from antarest.core.utils.string import to_camel_case


class ReservesGlobalParameters(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, extra="forbid", populate_by_name=True)

    reference_activation_duration_up: int = Field(default=1, ge=0)
    energy_activation_ratio_up: float = Field(default=1.0, ge=0.0, le=1.0)
    reference_activation_duration_down: int = Field(default=1, ge=0)
    energy_activation_ratio_down: float = Field(default=1.0, ge=0.0, le=1.0)


class ReservesGlobalParametersUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, extra="forbid", populate_by_name=True)

    reference_activation_duration_up: int | None = Field(default=None, ge=0)
    energy_activation_ratio_up: float | None = Field(default=None, ge=0.0, le=1.0)
    reference_activation_duration_down: int | None = Field(default=None, ge=0)
    energy_activation_ratio_down: float | None = Field(default=None, ge=0.0, le=1.0)


def update_reserves_global_parameters(
    current: ReservesGlobalParameters, update: ReservesGlobalParametersUpdate
) -> ReservesGlobalParameters:
    current_data = current.model_dump(mode="json")
    update_data = update.model_dump(mode="json", exclude_none=True)
    current_data.update(update_data)
    return ReservesGlobalParameters.model_validate(current_data)
