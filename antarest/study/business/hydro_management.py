from typing import Optional, Dict, Tuple, Any, TypedDict, List

from pydantic.types import StrictInt, StrictBool

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class ManagementOptionsFormFields(FormFieldsBaseModel):
    inter_daily_breakdown: Optional[StrictInt]
    intra_daily_modulation: Optional[StrictInt]
    inter_monthly_breakdown: Optional[StrictInt]
    reservoir: Optional[StrictBool]
    reservoir_capacity: Optional[StrictInt]
    follow_load: Optional[StrictBool]
    use_water: Optional[StrictBool]
    hard_bounds: Optional[StrictBool]
    initialize_reservoir_date: Optional[StrictInt]
    use_heuristic: Optional[StrictBool]
    power_to_level: Optional[StrictBool]
    leeway_low: Optional[StrictInt]
    leeway_up: Optional[StrictInt]
    pumping_efficiency: Optional[StrictInt]


class FieldInfo(TypedDict, total=False):
    path: str
    default_value: Any
    version: Optional[int]


HYDRO_PATH = "input/hydro/hydro"

FIELDS_INFO: Dict[str, FieldInfo] = {
    "inter_daily_breakdown": {
        "path": f"{HYDRO_PATH}/inter-daily-breakdown",
        "default_value": 1,
    },
    "intra_daily_modulation": {
        "path": f"{HYDRO_PATH}/intra-daily-modulation",
        "default_value": 24,
    },
    "inter_monthly_breakdown": {
        "path": f"{HYDRO_PATH}/inter-monthly-breakdown",
        "default_value": 1,
    },
    "reservoir": {"path": f"{HYDRO_PATH}/reservoir", "default_value": False},
    "reservoir_capacity": {
        "path": f"{HYDRO_PATH}/reservoir capacity",
        "default_value": 0,
    },
    "follow_load": {
        "path": f"{HYDRO_PATH}/follow load",
        "default_value": True,
    },
    "use_water": {"path": f"{HYDRO_PATH}/use water", "default_value": False},
    "hard_bounds": {
        "path": f"{HYDRO_PATH}/hard bounds",
        "default_value": False,
    },
    "initialize_reservoir_date": {
        "path": f"{HYDRO_PATH}/initialize reservoir date",
        "default_value": 0,
    },
    "use_heuristic": {
        "path": f"{HYDRO_PATH}/use heuristic",
        "default_value": True,
    },
    "power_to_level": {
        "path": f"{HYDRO_PATH}/power to level",
        "default_value": False,
    },
    "leeway_low": {"path": f"{HYDRO_PATH}/leeway low", "default_value": 1},
    "leeway_up": {"path": f"{HYDRO_PATH}/leeway up", "default_value": 1},
    "pumping_efficiency": {
        "path": f"{HYDRO_PATH}/pumping efficiency",
        "default_value": 1,
    },
}


class HydroManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(
        self, study: Study, area_id: str
    ) -> ManagementOptionsFormFields:
        """
        Get management options for a given area
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        hydro_config = file_study.tree.get(HYDRO_PATH.split("/"))

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            target_name = path.split("/")[-1]
            return hydro_config.get(target_name, {}).get(
                area_id, field_info["default_value"]
            )

        return ManagementOptionsFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self,
        study: Study,
        field_values: ManagementOptionsFormFields,
        area_id: str,
    ) -> None:
        """
        Set management options for a given area
        """
        commands: List[UpdateConfig] = []

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        target="/".join([info["path"], area_id]),
                        data=value,
                        command_context=self.storage_service.variant_study_service.command_factory.command_context,
                    )
                )

        if len(commands) > 0:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
