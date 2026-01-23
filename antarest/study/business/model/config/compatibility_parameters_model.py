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

from enum import StrEnum
from typing import Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import STUDY_VERSION_9_2


class HydroPmax(StrEnum):
    DAILY = "daily"
    HOURLY = "hourly"


class CompatibilityParameters(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    hydro_pmax: HydroPmax | None = None


class CompatibilityParametersUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    hydro_pmax: Optional[HydroPmax] = None


def update_compatibility_parameters(
    parameters: CompatibilityParameters, new_parameters: CompatibilityParametersUpdate
) -> CompatibilityParameters:
    current_properties = parameters.model_dump(mode="json")
    new_properties = new_parameters.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return CompatibilityParameters.model_validate(current_properties)


def validate_compatibility_parameters_against_version(
    version: StudyVersion, parameters_data: CompatibilityParameters | CompatibilityParametersUpdate
) -> None:
    if version < STUDY_VERSION_9_2 and parameters_data.hydro_pmax is not None:
        raise InvalidFieldForVersionError("Hydro pmax cannot be set to hourly before study version 9.2")
