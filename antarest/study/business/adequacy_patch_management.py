# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from typing import Any, Dict, List

from pydantic.types import StrictBool, confloat, conint

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_8_5, Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class PriceTakingOrder(EnumIgnoreCase):
    DENS = "DENS"
    LOAD = "Load"


ThresholdType = confloat(ge=0)


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
    threshold_initiate_curtailment_sharing_rule: ThresholdType  # type: ignore
    threshold_display_local_matching_rule_violations: ThresholdType  # type: ignore
    threshold_csr_variable_bounds_relaxation: conint(ge=0, strict=True)  # type: ignore


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
        "default_value": 0.0,
        "start_version": STUDY_VERSION_8_5,
    },
    "threshold_display_local_matching_rule_violations": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-display-local-matching-rule-violations",
        "default_value": 0.0,
        "start_version": STUDY_VERSION_8_5,
    },
    "threshold_csr_variable_bounds_relaxation": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-csr-variable-bounds-relaxation",
        "default_value": 3,
        "start_version": STUDY_VERSION_8_5,
    },
}


class AdequacyPatchManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> AdequacyPatchFormFields:
        """
        Get adequacy patch field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        parent = general_data.get("adequacy patch", {})

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            start_version = field_info.get("start_version", -1)
            target_name = path.split("/")[-1]
            is_in_version = file_study.config.version >= start_version

            return parent.get(target_name, field_info["default_value"]) if is_in_version else None

        return AdequacyPatchFormFields.construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(self, study: Study, field_values: AdequacyPatchFormFields) -> None:
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
                        command_context=self.storage_service.variant_study_service.command_factory.command_context,
                        study_version=study.version,
                    )
                )

        if commands:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(study, file_study, commands, self.storage_service)
