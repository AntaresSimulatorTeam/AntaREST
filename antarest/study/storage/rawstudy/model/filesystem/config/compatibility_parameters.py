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
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    validate_compatibility_parameters_against_version,
)


class CompatibilitySection(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    hydro_pmax: str | None = None


class CompatibilityParametersFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    compatibility: CompatibilitySection | None = Field(default=None, alias="compatibility")

    def to_model(self) -> CompatibilityParameters:
        args = {}
        if self.compatibility:
            args.update(self.compatibility.model_dump(exclude_none=True))
        return CompatibilityParameters.model_validate(args)

    @classmethod
    def from_model(cls, parameters: CompatibilityParameters) -> "CompatibilityParametersFileData":
        args = {}
        args["compatibility"] = parameters.model_dump(include=set(CompatibilitySection.model_fields))
        return cls.model_validate(args)


def parse_compatibility_parameters(version: StudyVersion, data: dict[str, Any]) -> CompatibilityParameters:
    parameters = CompatibilityParametersFileData.model_validate(data).to_model()
    validate_compatibility_parameters_against_version(version, parameters)
    return parameters
