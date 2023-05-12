from enum import Enum
from typing import Optional, Union, List, Any, Dict, cast

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


class LegacyTransmissionCapacities(str, Enum):
    INFINITE = "infinite"


class TransmissionCapacities(str, Enum):
    LOCAL_VALUES = "local-values"
    NULL_FOR_ALL_LINKS = "null-for-all-links"
    INFINITE_FOR_ALL_LINKS = "infinite-for-all-links"
    NULL_FOR_PHYSICAL_LINKS = "null-for-physical-links"
    INFINITE_FOR_PHYSICAL_LINKS = "infinite-for-physical-links"


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
    transmission_capacities: Optional[
        Union[
            StrictBool,
            Union[LegacyTransmissionCapacities, TransmissionCapacities],
        ]
    ]
    thermal_clusters_min_stable_power: Optional[StrictBool]
    thermal_clusters_min_ud_time: Optional[StrictBool]
    day_ahead_reserve: Optional[StrictBool]
    primary_reserve: Optional[StrictBool]
    strategic_reserve: Optional[StrictBool]
    spinning_reserve: Optional[StrictBool]
    export_mps: Optional[Union[bool, str]]
    unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior]
    simplex_optimization_range: Optional[SimplexOptimizationRange]


OPTIMIZATION_PATH = f"{GENERAL_DATA_PATH}/optimization"


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
        "default_value": UnfeasibleProblemBehavior.ERROR_VERBOSE.value,
    },
    "simplex_optimization_range": {
        "path": f"{OPTIMIZATION_PATH}/simplex-range",
        "default_value": SimplexOptimizationRange.WEEK.value,
    },
}


class OptimizationManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> OptimizationFormFields:
        """
        Get optimization field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        parent = general_data.get("optimization", {})

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            study_ver = file_study.config.version
            start_ver = cast(int, field_info.get("start_version", -1))
            target_name = path.split("/")[-1]
            is_in_version = start_ver <= study_ver

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
        Set optimization config from the webapp form
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
