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
from typing import Annotated, Any, Optional, TypeAlias

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import (
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_5,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
)


class PriceTakingOrder(EnumIgnoreCase):
    DENS = "DENS"
    LOAD = "Load"


ThresholdType: TypeAlias = Annotated[Optional[float], Field(default=None, ge=0)]


class AdequacyPatchParameters(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    # Since v8.3
    enable_adequacy_patch: bool = False
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool = True
    # Since v8.5
    price_taking_order: Optional[PriceTakingOrder] = None
    include_hurdle_cost_csr: Optional[bool] = None
    check_csr_cost_function: Optional[bool] = None
    threshold_initiate_curtailment_sharing_rule: ThresholdType
    threshold_display_local_matching_rule_violations: ThresholdType
    threshold_csr_variable_bounds_relaxation: Optional[int] = Field(default=None, ge=0)
    # Appeared in v8.3 and removed in v9.2
    ntc_between_physical_areas_out_adequacy_patch: Optional[bool] = None
    # Since v9.3
    redispatch: Optional[bool] = None


class AdequacyPatchParametersUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    enable_adequacy_patch: Optional[bool] = None
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: Optional[bool] = None
    price_taking_order: Optional[PriceTakingOrder] = None
    include_hurdle_cost_csr: Optional[bool] = None
    check_csr_cost_function: Optional[bool] = None
    threshold_initiate_curtailment_sharing_rule: ThresholdType
    threshold_display_local_matching_rule_violations: ThresholdType
    threshold_csr_variable_bounds_relaxation: Optional[int] = Field(default=None, ge=0)
    ntc_between_physical_areas_out_adequacy_patch: Optional[bool] = None
    redispatch: Optional[bool] = None


def update_adequacy_patch_parameters(
    parameters: AdequacyPatchParameters, new_parameters: AdequacyPatchParametersUpdate
) -> AdequacyPatchParameters:
    """
    Updates the adequacy patch parameters according to the provided update data.
    """
    current_properties = parameters.model_dump(mode="json")
    new_properties = new_parameters.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return AdequacyPatchParameters.model_validate(current_properties)


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_adequacy_patch_parameters_against_version(
    version: StudyVersion,
    parameters_data: AdequacyPatchParameters | AdequacyPatchParametersUpdate,
) -> None:
    """
    Validates input adequacy patch parameters data against the provided study versions
    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_8_3:
        raise InvalidFieldForVersionError("Adequacy patch parameters only exists in v8.3+ studies")

    if version < STUDY_VERSION_8_5:
        for field in [
            "price_taking_order",
            "include_hurdle_cost_csr",
            "check_csr_cost_function",
            "threshold_initiate_curtailment_sharing_rule",
            "threshold_display_local_matching_rule_violations",
            "threshold_csr_variable_bounds_relaxation",
        ]:
            _check_min_version(parameters_data, field, version)

    if version < STUDY_VERSION_9_3:
        _check_min_version(parameters_data, "redispatch", version)

    if version >= STUDY_VERSION_9_2:
        _check_min_version(parameters_data, "ntc_between_physical_areas_out_adequacy_patch", version)


def _initialize_field_default(parameters: AdequacyPatchParameters, field: str, default_value: Any) -> None:
    if getattr(parameters, field) is None:
        setattr(parameters, field, default_value)


def _reset_field(parameters: AdequacyPatchParameters, field: str) -> None:
    setattr(parameters, field, None)


def initialize_adequacy_patch_parameters(parameters: AdequacyPatchParameters, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version >= STUDY_VERSION_8_3:
        _initialize_field_default(parameters, "ntc_between_physical_areas_out_adequacy_patch", True)

    if version >= STUDY_VERSION_8_5:
        _initialize_field_default(parameters, "price_taking_order", PriceTakingOrder.DENS)
        _initialize_field_default(parameters, "include_hurdle_cost_csr", False)
        _initialize_field_default(parameters, "check_csr_cost_function", False)
        _initialize_field_default(parameters, "threshold_initiate_curtailment_sharing_rule", 1)
        _initialize_field_default(parameters, "threshold_display_local_matching_rule_violations", 0)
        _initialize_field_default(parameters, "threshold_csr_variable_bounds_relaxation", 7)

    if version >= STUDY_VERSION_9_2:
        _reset_field(parameters, "ntc_between_physical_areas_out_adequacy_patch")

    if version >= STUDY_VERSION_9_3:
        _initialize_field_default(parameters, "redispatch", False)
