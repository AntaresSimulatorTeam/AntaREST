from enum import Enum
from typing import Optional, List, Any, Dict

from pydantic.types import StrictBool, StrictFloat, StrictInt

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
    FieldInfo,
    GENERAL_DATA_PATH,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class PriceTakingOrder(str, Enum):
    DENS = "DENS"
    LOAD = "Load"


class AdequacyPatchFormFields(FormFieldsBaseModel):
    # version 830
    enable_adequacy_patch: Optional[StrictBool]
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: Optional[
        StrictBool
    ]
    ntc_between_physical_areas_out_adequacy_patch: Optional[StrictBool]
    # version 850
    price_taking_order: Optional[PriceTakingOrder]
    include_hurdle_cost_csr: Optional[StrictBool]
    check_csr_cost_function: Optional[StrictBool]
    threshold_initiate_curtailment_sharing_rule: Optional[StrictFloat]
    threshold_display_local_matching_rule_violations: Optional[StrictFloat]
    threshold_csr_variable_bounds_relaxation: Optional[StrictInt]


ADEQUACY_PATCH_PATH = f"{GENERAL_DATA_PATH}/adequacy patch"


FIELDS_INFO: Dict[str, FieldInfo] = {
    "enable_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/include-adq-patch",
        "default_value": False,
        "start_version": 830,
    },
    "ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/set-to-null-ntc-from-physical-out-to-physical-in-for-first-step",
        "default_value": True,
        "start_version": 830,
    },
    "ntc_between_physical_areas_out_adequacy_patch": {
        "path": f"{ADEQUACY_PATCH_PATH}/set-to-null-ntc-between-physical-out-for-first-step",
        "default_value": True,
        "start_version": 830,
    },
    "price_taking_order": {
        "path": f"{ADEQUACY_PATCH_PATH}/price-taking-order",
        "default_value": PriceTakingOrder.DENS.value,
        "start_version": 850,
    },
    "include_hurdle_cost_csr": {
        "path": f"{ADEQUACY_PATCH_PATH}/include-hurdle-cost-csr",
        "default_value": False,
        "start_version": 850,
    },
    "check_csr_cost_function": {
        "path": f"{ADEQUACY_PATCH_PATH}/check-csr-cost-function",
        "default_value": False,
        "start_version": 850,
    },
    "threshold_initiate_curtailment_sharing_rule": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-initiate-curtailment-sharing-rule",
        "default_value": 0.0,
        "start_version": 850,
    },
    "threshold_display_local_matching_rule_violations": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-display-local-matching-rule-violations",
        "default_value": 0.0,
        "start_version": 850,
    },
    "threshold_csr_variable_bounds_relaxation": {
        "path": f"{ADEQUACY_PATCH_PATH}/threshold-csr-variable-bounds-relaxation",
        "default_value": 3,
        "start_version": 850,
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
            is_in_version = file_study.config.version >= start_version  # type: ignore

            return (
                parent.get(target_name, field_info["default_value"])
                if is_in_version
                else None
            )

        return AdequacyPatchFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self, study: Study, field_values: AdequacyPatchFormFields
    ) -> None:
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
                    )
                )

        if commands:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
