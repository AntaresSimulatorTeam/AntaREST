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
from typing import Annotated, Any, Dict, List, TypeAlias

from pydantic import Field
from pydantic.types import StrictBool

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo, FormFieldsBaseModel
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_8_5, STUDY_VERSION_9_2
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class PriceTakingOrder(EnumIgnoreCase):
    DENS = "DENS"
    LOAD = "Load"


ThresholdType: TypeAlias = Annotated[float, Field(ge=0)]


@all_optional_model
class AdequacyPatchFormFields(FormFieldsBaseModel):
    # version 830
    enable_adequacy_patch: StrictBool
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: StrictBool
    ntc_between_physical_areas_out_adequacy_patch: StrictBool
    # version 850
    price_taking_order: PriceTakingOrder
    include_hurdle_cost_csr: StrictBool
    check_csr_cost_function: StrictBool
    threshold_initiate_curtailment_sharing_rule: ThresholdType
    threshold_display_local_matching_rule_violations: ThresholdType
    threshold_csr_variable_bounds_relaxation: Annotated[int, Field(ge=0, strict=True)]


ADEQUACY_PATCH_PATH = f"{GENERAL_DATA_PATH}/adequacy patch"


FIELDS_INFO: Dict[str, FieldInfo] = {
    "enable_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/include-adq-patch",
        "default_value": False,
        "start_version": STUDY_VERSION_8_3,
    },
    "ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/set-to-null-ntc-from-physical-out-to-physical-in-for-first-step",
        "default_value": True,
        "start_version": STUDY_VERSION_8_3,
    },
    "ntc_between_physical_areas_out_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/set-to-null-ntc-between-physical-out-for-first-step",
        "default_value": True,
        "start_version": STUDY_VERSION_8_3,
        "end_version": STUDY_VERSION_9_2,
    },
    "price_taking_order": {
        "path": f"{ADEQUACY_PATCH_PATH}/price-taking-order",
        "default_value": PriceTakingOrder.DENS.value,
        "start_version": STUDY_VERSION_8_5,
    },
    "include_hurdle_cost_csr": {
        "path": f"{ADEQUACY_PATCH_PATH}/include-hurdle-cost-csr",
        "default_value": False,
        "start_version": STUDY_VERSION_8_5,
    },
    "check_csr_cost_function": {
        "path": f"{ADEQUACY_PATCH_PATH}/check-csr-cost-function",
        "default_value": False,
        "start_version": STUDY_VERSION_8_5,
    },
    "threshold_initiate_curtailment_sharing_rule": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-initiate-curtailment-sharing-rule",
        "default_value": 1.0,
        "start_version": STUDY_VERSION_8_5,
    },
    "threshold_display_local_matching_rule_violations": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-display-local-matching-rule-violations",
        "default_value": 0.0,
        "start_version": STUDY_VERSION_8_5,
    },
    "threshold_csr_variable_bounds_relaxation": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-csr-variable-bounds-relaxation",
        "default_value": 7,
        "start_version": STUDY_VERSION_8_5,
    },
}


class AdequacyPatchManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface) -> AdequacyPatchFormFields:
        """
        Get adequacy patch field values for the webapp form
        """
        file_study = study.get_files()
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        parent = general_data.get("adequacy patch", {})

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            start_version = field_info.get("start_version", 0)
            end_version = field_info.get("end_version", 10000)
            target_name = path.split("/")[-1]
            is_in_version = study.version >= start_version and file_study.config.version < end_version

            return parent.get(target_name, field_info["default_value"]) if is_in_version else None

        return AdequacyPatchFormFields.model_construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(self, study: StudyInterface, field_values: AdequacyPatchFormFields) -> None:
        """
        Set adequacy patch config from the webapp form
        """
        commands: List[UpdateConfig] = []

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        target=info["path"],
                        data=value,
                        command_context=self._command_context,
                        study_version=study.version,
                    )
                )

        if commands:
            study.add_commands(commands)
