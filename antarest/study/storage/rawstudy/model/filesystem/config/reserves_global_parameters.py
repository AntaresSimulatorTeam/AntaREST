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

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.reserve_definition_model import GLOBAL_PARAMETERS_SECTION
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters


class ReservesGlobalParametersFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    reference_activation_duration_up: int = 1
    energy_activation_ratio_up: float = 1.0
    reference_activation_duration_down: int = 1
    energy_activation_ratio_down: float = 1.0

    def to_model(self) -> ReservesGlobalParameters:
        return ReservesGlobalParameters.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, parameters: ReservesGlobalParameters) -> "ReservesGlobalParametersFileData":
        return cls.model_validate(parameters.model_dump())


def parse_reserves_global_parameters(data: dict[str, Any]) -> ReservesGlobalParameters:
    global_params_data = data.get(GLOBAL_PARAMETERS_SECTION, {})
    return ReservesGlobalParametersFileData.model_validate(global_params_data).to_model()


def serialize_reserves_global_parameters(parameters: ReservesGlobalParameters) -> dict[str, Any]:
    return ReservesGlobalParametersFileData.from_model(parameters).model_dump(mode="json", by_alias=True)
