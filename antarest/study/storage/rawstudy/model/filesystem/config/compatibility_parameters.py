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

from antares.study.version import StudyVersion
from pydantic import ConfigDict, field_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    HydroPmax,
    validate_compatibility_parameters_against_version,
)


class CompatibilityParametersFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    hydro_pmax: HydroPmax | None = None

    @field_validator("hydro_pmax", mode="before")
    @classmethod
    def validate_hydro_pmax(cls, v: Any) -> Any:
        """Convert old format 'HydroPmax.HOURLY' or 'HydroPmax.DAILY' to enum values."""
        if isinstance(v, str):
            if v == "HydroPmax.HOURLY":
                return "hourly"
            elif v == "HydroPmax.DAILY":
                return "daily"
            elif v in ("hourly", "daily"):
                return v
        return v

    def to_model(self) -> CompatibilityParameters:
        return CompatibilityParameters.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, parameters: CompatibilityParameters) -> "CompatibilityParametersFileData":
        return cls.model_validate(parameters.model_dump())


def parse_compatibility_parameters(version: StudyVersion, data: dict[str, Any]) -> CompatibilityParameters:
    # Extract the compatibility section if it exists, otherwise use empty dict
    compatibility_data = data.get("compatibility", {})
    parameters = CompatibilityParametersFileData.model_validate(compatibility_data).to_model()
    validate_compatibility_parameters_against_version(version, parameters)
    return parameters
