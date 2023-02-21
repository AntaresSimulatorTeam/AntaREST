from enum import Enum
from pathlib import PurePosixPath
from typing import Optional, Dict, Any, List

from pydantic import StrictStr, StrictInt, StrictBool

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    FieldInfo,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class TimeSeriesGenerationOption(str, Enum):
    USE_GLOBAL_PARAMETER = "use global parameter"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(str, Enum):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


THERMAL_PATH = "input/thermal/clusters/{area}/list/{cluster}"


class ThermalFormFields(FormFieldsBaseModel):
    group: Optional[StrictStr]
    name: Optional[StrictStr]
    unit_count: Optional[StrictInt]
    enabled: Optional[StrictBool]
    nominal_capacity: Optional[StrictInt]
    gen_ts: Optional[TimeSeriesGenerationOption]
    min_stable_power: Optional[StrictInt]
    min_up_time: Optional[StrictInt]
    min_down_time: Optional[StrictInt]
    must_run: Optional[StrictBool]
    spinning: Optional[StrictInt]
    co2: Optional[StrictInt]
    volatility_forced: Optional[StrictInt]
    volatility_planned: Optional[StrictInt]
    law_forced: Optional[LawOption]
    law_planned: Optional[LawOption]
    marginal_cost: Optional[StrictInt]
    spread_cost: Optional[StrictInt]
    fixed_cost: Optional[StrictInt]
    startup_cost: Optional[StrictInt]
    market_bid_cost: Optional[StrictInt]


FIELDS_INFO: Dict[str, FieldInfo] = {
    "group": {
        "path": f"{THERMAL_PATH}/group",
        "default_value": "",
    },
    "name": {
        "path": f"{THERMAL_PATH}/name",
        "default_value": "",
    },
    "unit_count": {
        "path": f"{THERMAL_PATH}/unitcount",
        "default_value": 0,
    },
    "enabled": {
        "path": f"{THERMAL_PATH}/enabled",
        "default_value": True,
    },
    "nominal_capacity": {
        "path": f"{THERMAL_PATH}/nominalcapacity",
        "default_value": 0,
    },
    "gen_ts": {
        "path": f"{THERMAL_PATH}/gen-ts",
        "default_value": TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER.value,
    },
    "min_stable_power": {
        "path": f"{THERMAL_PATH}/min-stable-power",
        "default_value": 0,
    },
    "min_up_time": {
        "path": f"{THERMAL_PATH}/min-up-time",
        "default_value": 1,
    },
    "min_down_time": {
        "path": f"{THERMAL_PATH}/min-down-time",
        "default_value": 1,
    },
    "must_run": {
        "path": f"{THERMAL_PATH}/must-run",
        "default_value": False,
    },
    "spinning": {
        "path": f"{THERMAL_PATH}/spinning",
        "default_value": 0,
    },
    "co2": {
        "path": f"{THERMAL_PATH}/co2",
        "default_value": 0,
    },
    "volatility_forced": {
        "path": f"{THERMAL_PATH}/volatility.forced",
        "default_value": 0,
    },
    "volatility_planned": {
        "path": f"{THERMAL_PATH}/volatility.planned",
        "default_value": 0,
    },
    "law_forced": {
        "path": f"{THERMAL_PATH}/law.forced",
        "default_value": LawOption.UNIFORM.value,
    },
    "law_planned": {
        "path": f"{THERMAL_PATH}/law.planned",
        "default_value": LawOption.UNIFORM.value,
    },
    "marginal_cost": {
        "path": f"{THERMAL_PATH}/marginal-cost",
        "default_value": 0,
    },
    "spread_cost": {
        "path": f"{THERMAL_PATH}/spread-cost",
        "default_value": 0,
    },
    "fixed_cost": {
        "path": f"{THERMAL_PATH}/fixed-cost",
        "default_value": 0,
    },
    "startup_cost": {
        "path": f"{THERMAL_PATH}/startup-cost",
        "default_value": 0,
    },
    "market_bid_cost": {
        "path": f"{THERMAL_PATH}/market-bid-cost",
        "default_value": 0,
    },
}


def format_path(path: str, area_id: str, cluster_id: str) -> str:
    return path.format(area=area_id, cluster=cluster_id)


class ThermalManager:
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_field_values(
        self, study: Study, area_id: str, cluster_id: str
    ) -> ThermalFormFields:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        thermal_config = file_study.tree.get(
            format_path(THERMAL_PATH, area_id, cluster_id).split("/")
        )

        def get_value(field_info: FieldInfo) -> Any:
            target_name = PurePosixPath(field_info["path"]).name
            return thermal_config.get(target_name, field_info["default_value"])

        return ThermalFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        field_values: ThermalFormFields,
    ) -> None:
        commands: List[UpdateConfig] = []

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                commands.append(
                    UpdateConfig(
                        target=format_path(info["path"], area_id, cluster_id),
                        data=value,
                        command_context=self.storage_service.variant_study_service.command_factory.command_context,
                    )
                )

        if commands:
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
