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
from typing import Any

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParameters,
    PriceTakingOrder,
    initialize_adequacy_patch_parameters,
    validate_adequacy_patch_parameters_against_version,
)


class AdequacyPatchParametersFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    enable_adequacy_patch: bool | None = Field(default=None, alias="include-adq-patch")
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool | None = Field(
        default=None, alias="set-to-null-ntc-from-physical-out-to-physical-in-for-first-step"
    )
    price_taking_order: PriceTakingOrder | None = None
    include_hurdle_cost_csr: bool | None = None
    check_csr_cost_function: bool | None = None
    threshold_initiate_curtailment_sharing_rule: float | None = None
    threshold_display_local_matching_rule_violations: float | None = None
    threshold_csr_variable_bounds_relaxation: int | None = None
    ntc_between_physical_areas_out_adequacy_patch: bool | None = Field(
        default=None, alias="set-to-null-ntc-between-physical-out-for-first-step"
    )
    redispatch: bool | None = None

    def to_model(self) -> AdequacyPatchParameters:
        return AdequacyPatchParameters.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, parameters: AdequacyPatchParameters) -> "AdequacyPatchParametersFileData":
        return cls.model_validate(parameters.model_dump())


def parse_adequacy_patch_parameters(version: StudyVersion, data: dict[str, Any]) -> AdequacyPatchParameters:
    parameters = AdequacyPatchParametersFileData.model_validate(data).to_model()
    validate_adequacy_patch_parameters_against_version(version, parameters)
    initialize_adequacy_patch_parameters(parameters, version)
    return parameters


def serialize_adequacy_patch_parameters(version: StudyVersion, parameters: AdequacyPatchParameters) -> dict[str, Any]:
    validate_adequacy_patch_parameters_against_version(version, parameters)
    internal_model = AdequacyPatchParametersFileData.from_model(parameters)
    return internal_model.model_dump(mode="json", by_alias=True, exclude_none=True)
