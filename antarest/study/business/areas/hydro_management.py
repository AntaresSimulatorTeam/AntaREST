from typing import Any, Dict, List, Optional, Union

from pydantic import Field, model_validator

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

INFLOW_PATH = "input/hydro/prepro/{area_id}/prepro/prepro"


class InflowStructure(FormFieldsBaseModel):
    """Represents the inflow structure values in the hydraulic configuration."""

    # NOTE: Currently, there is only one field for the inflow structure model
    # due to the scope of hydro config requirements, it may change.
    inter_monthly_correlation: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


@all_optional_model
class ManagementOptionsFormFields(FormFieldsBaseModel):
    inter_daily_breakdown: float
    intra_daily_modulation: float
    inter_monthly_breakdown: float
    reservoir: bool
    reservoir_capacity: float
    follow_load: bool
    use_water: bool
    hard_bounds: bool
    initialize_reservoir_date: int
    use_heuristic: bool
    power_to_level: bool
    use_leeway: bool
    leeway_low: float
    leeway_up: float
    pumping_efficiency: float

    @model_validator(mode="before")
    def check_type_validity(cls, values: Dict[str, Any]) -> Dict[str, Optional[Any]]:
        cls.validate_ge("inter_daily_breakdown", values.get("inter_daily_breakdown", 0), 0)
        cls.validate_ge("intra_daily_modulation", values.get("intra_daily_modulation", 1), 1)
        cls.validate_ge("inter_monthly_breakdown", values.get("inter_monthly_breakdown", 0), 0)
        cls.validate_ge("reservoir_capacity", values.get("reservoir_capacity", 0), 0)
        cls.validate_ge("initialize_reservoir_date", values.get("initialize_reservoir_date", 0), 0)
        cls.validate_le("initialize_reservoir_date", values.get("initialize_reservoir_date", 11), 11)
        cls.validate_ge("leeway_low", values.get("leeway_low", 0), 0)
        cls.validate_ge("leeway_up", values.get("leeway_up", 0), 0)
        cls.validate_ge("pumping_efficiency", values.get("pumping_efficiency", 0), 0)
        return values

    @staticmethod
    def validate_ge(field: str, value: Union[int, float], ge: int) -> None:
        if value < ge:
            raise ValueError(f"Field {field} must be greater than or equal to {ge}")

    @staticmethod
    def validate_le(field: str, value: Union[int, float], le: int) -> None:
        if value > le:
            raise ValueError(f"Field {field} must be lower than or equal to {le}")


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
    "use_leeway": {"path": f"{HYDRO_PATH}/use leeway", "default_value": False},
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

    def get_field_values(self, study: Study, area_id: str) -> ManagementOptionsFormFields:
        """
        Get management options for a given area
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        hydro_config = file_study.tree.get(HYDRO_PATH.split("/"))

        def get_value(field_info: FieldInfo) -> Any:
            path = field_info["path"]
            target_name = path.split("/")[-1]
            return hydro_config.get(target_name, {}).get(area_id, field_info["default_value"])

        return ManagementOptionsFormFields.construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

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
            execute_or_add_commands(study, file_study, commands, self.storage_service)

    # noinspection SpellCheckingInspection
    def get_inflow_structure(self, study: Study, area_id: str) -> InflowStructure:
        """
        Retrieves inflow structure values for a specific area within a study.

        Returns:
            InflowStructure: The inflow structure values.
        """
        # NOTE: Focusing on the single field "intermonthly-correlation" due to current model scope.
        path = INFLOW_PATH.format(area_id=area_id)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        inter_monthly_correlation = file_study.tree.get(path.split("/")).get("intermonthly-correlation", 0.5)
        return InflowStructure(inter_monthly_correlation=inter_monthly_correlation)

    # noinspection SpellCheckingInspection
    def update_inflow_structure(self, study: Study, area_id: str, values: InflowStructure) -> None:
        """
        Updates inflow structure values for a specific area within a study.

        Args:
            study: The study instance to update the inflow data for.
            area_id: The area identifier to update data for.
            values: The new inflow structure values to be updated.

        Raises:
            ValidationError: If the provided `values` parameter is None or invalid.
        """
        # NOTE: Updates only "intermonthly-correlation" due to current model scope.
        path = INFLOW_PATH.format(area_id=area_id)
        command = UpdateConfig(
            target=path,
            data={"intermonthly-correlation": values.inter_monthly_correlation},
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(study, file_study, [command], self.storage_service)
