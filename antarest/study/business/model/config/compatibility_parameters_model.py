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

from antares.study.version import StudyVersion
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import STUDY_VERSION_9_2, STUDY_VERSION_10_2


class HydroPmax(StrEnum):
    DAILY = "daily"
    HOURLY = "hourly"


class HydroRuleCurves(StrEnum):
    SCENARIZED = "scenarized"
    SINGLE = "single"


class CompatibilityParameters(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    hydro_pmax: HydroPmax = HydroPmax.DAILY
    # v10.2 field
    hydro_rule_curves: HydroRuleCurves | None = None


class CompatibilityParametersUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    hydro_pmax: HydroPmax | None = None
    hydro_rule_curves: HydroRuleCurves | None = None


def update_compatibility_parameters(
    parameters: CompatibilityParameters, new_parameters: CompatibilityParametersUpdate
) -> CompatibilityParameters:
    current_properties = parameters.model_dump(mode="json")
    new_properties = new_parameters.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return CompatibilityParameters.model_validate(current_properties)


def initialize_compatibility_parameters(parameters: CompatibilityParameters, version: StudyVersion) -> None:
    if version >= STUDY_VERSION_10_2 and parameters.hydro_rule_curves is None:
        parameters.hydro_rule_curves = HydroRuleCurves.SINGLE


def validate_compatibility_parameters_against_version(
    version: StudyVersion, parameters: CompatibilityParametersUpdate | CompatibilityParameters
) -> None:
    if parameters.hydro_pmax is not None and version < STUDY_VERSION_9_2:
        raise InvalidFieldForVersionError("Hydro pmax cannot be set to hourly before study version 9.2")
    if parameters.hydro_rule_curves is not None and version < STUDY_VERSION_10_2:
        raise InvalidFieldForVersionError("Hydro rule curves cannot be set to scenarized before study version 10.2")
