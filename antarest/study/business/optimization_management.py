from enum import Enum
from typing import Optional, Union, Literal, List, Any, Dict, TypedDict

from pydantic.types import StrictBool

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


class LinkType(str, Enum):
    LOCAL = "local"
    AC = "ac"


class UnfeasibleProblemBehavior(str, Enum):
    WARNING_DRY = "warning-dry"
    WARNING_VERBOSE = "warning-verbose"
    ERROR_DRY = "error-dry"
    ERROR_VERBOSE = "error-verbose"


class SimplexOptimizationRange(str, Enum):
    DAY = "day"
    WEEK = "week"


class OptimizationFormFields(FormFieldsBaseModel):
    binding_constraints: Optional[StrictBool]
    hurdle_costs: Optional[StrictBool]
    transmission_capacities: Optional[Union[StrictBool, Literal["infinite"]]]
    link_type: Optional[LinkType]
    thermal_clusters_min_stable_power: Optional[StrictBool]
    thermal_clusters_min_ud_time: Optional[StrictBool]
    day_ahead_reserve: Optional[StrictBool]
    primary_reserve: Optional[StrictBool]
    strategic_reserve: Optional[StrictBool]
    spinning_reserve: Optional[StrictBool]
    export_mps: Optional[StrictBool]
    unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior]
    simplex_optimization_range: Optional[SimplexOptimizationRange]
    # version 830
    split_exported_mps: Optional[StrictBool]
    enable_adequacy_patch: Optional[StrictBool]
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: Optional[
        StrictBool
    ]
    ntc_between_physical_areas_out_adequacy_patch: Optional[StrictBool]


OPTIMIZATION_PATH = f"{GENERAL_DATA_PATH}/optimization"
ADEQUACY_PATCH_PATH = f"{GENERAL_DATA_PATH}/adequacy patch"


FIELDS_INFO: Dict[str, FieldInfo] = {
    "binding_constraints": {
        "path": f"{OPTIMIZATION_PATH}/include-constraints",
        "default_value": True,
    },
    "hurdle_costs": {
        "path": f"{OPTIMIZATION_PATH}/include-hurdlecosts",
        "default_value": True,
    },
    "transmission_capacities": {
        "path": f"{OPTIMIZATION_PATH}/transmission-capacities",
        "default_value": True,
    },
    "link_type": {
        "path": f"{OPTIMIZATION_PATH}/link-type",
        "default_value": LinkType.LOCAL,
    },
    "thermal_clusters_min_stable_power": {
        "path": f"{OPTIMIZATION_PATH}/include-tc-minstablepower",
        "default_value": True,
    },
    "thermal_clusters_min_ud_time": {
        "path": f"{OPTIMIZATION_PATH}/include-tc-min-ud-time",
        "default_value": True,
    },
    "day_ahead_reserve": {
        "path": f"{OPTIMIZATION_PATH}/include-dayahead",
        "default_value": True,
    },
    "primary_reserve": {
        "path": f"{OPTIMIZATION_PATH}/include-primaryreserve",
        "default_value": True,
    },
    "strategic_reserve": {
        "path": f"{OPTIMIZATION_PATH}/include-strategicreserve",
        "default_value": True,
    },
    "spinning_reserve": {
        "path": f"{OPTIMIZATION_PATH}/include-spinningreserve",
        "default_value": True,
    },
    "export_mps": {
        "path": f"{OPTIMIZATION_PATH}/include-exportmps",
        "default_value": False,
    },
    "unfeasible_problem_behavior": {
        "path": f"{OPTIMIZATION_PATH}/include-unfeasible-problem-behavior",
        "default_value": UnfeasibleProblemBehavior.ERROR_VERBOSE,
    },
    "simplex_optimization_range": {
        "path": f"{OPTIMIZATION_PATH}/simplex-range",
        "default_value": SimplexOptimizationRange.WEEK,
    },
    "split_exported_mps": {
        "path": f"{OPTIMIZATION_PATH}/include-split-exported-mps",
        "default_value": False,
        "start_version": 830,
    },
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
}


class OptimizationManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> OptimizationFormFields:
        """
        Get Optimization field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        optimization = general_data.get("optimization", {})
        adequacy_patch = general_data.get("adequacy patch", {})

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            start_version = field_info.get("start_version", -1)
            target_name = path.split("/")[-1]
            is_in_version = file_study.config.version >= start_version  # type: ignore
            parent = (
                optimization if OPTIMIZATION_PATH in path else adequacy_patch
            )
            return (
                parent.get(target_name, field_info["default_value"])
                if is_in_version
                else None
            )

        return OptimizationFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self, study: Study, field_values: OptimizationFormFields
    ) -> None:
        """
        Set Optimization config from the webapp form
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

        if len(commands) > 0:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
