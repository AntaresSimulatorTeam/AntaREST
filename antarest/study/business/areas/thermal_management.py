from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, cast

from pydantic import StrictBool, StrictStr

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class TimeSeriesGenerationOption(EnumIgnoreCase):
    USE_GLOBAL_PARAMETER = "use global parameter"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class LawOption(EnumIgnoreCase):
    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


THERMAL_PATH = "input/thermal/clusters/{area}/list/{cluster}"


class ThermalFormFields(FormFieldsBaseModel):
    group: Optional[StrictStr]
    name: Optional[StrictStr]
    unit_count: Optional[int]
    enabled: Optional[StrictBool]
    nominal_capacity: Optional[int]
    gen_ts: Optional[TimeSeriesGenerationOption]
    min_stable_power: Optional[int]
    min_up_time: Optional[int]
    min_down_time: Optional[int]
    must_run: Optional[StrictBool]
    spinning: Optional[int]
    volatility_forced: Optional[int]
    volatility_planned: Optional[int]
    law_forced: Optional[LawOption]
    law_planned: Optional[LawOption]
    marginal_cost: Optional[int]
    spread_cost: Optional[int]
    fixed_cost: Optional[int]
    startup_cost: Optional[int]
    market_bid_cost: Optional[int]
    # Pollutants
    co2: Optional[float]
    so2: Optional[float]
    nh3: Optional[float]
    nox: Optional[float]
    nmvoc: Optional[float]
    pm25: Optional[float]
    pm5: Optional[float]
    pm10: Optional[float]
    op1: Optional[float]
    op2: Optional[float]
    op3: Optional[float]
    op4: Optional[float]
    op5: Optional[float]


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
    # Pollutants
    "co2": {
        "path": f"{THERMAL_PATH}/co2",
        "default_value": 0.0,
    },
    "so2": {
        "path": f"{THERMAL_PATH}/so2",
        "default_value": 0.0,
        "start_version": 860,
    },
    "nh3": {
        "path": f"{THERMAL_PATH}/nh3",
        "default_value": 0.0,
        "start_version": 860,
    },
    "nox": {
        "path": f"{THERMAL_PATH}/nox",
        "default_value": 0.0,
        "start_version": 860,
    },
    "nmvoc": {
        "path": f"{THERMAL_PATH}/nmvoc",
        "default_value": 0.0,
        "start_version": 860,
    },
    "pm25": {
        "path": f"{THERMAL_PATH}/pm2_5",
        "default_value": 0.0,
        "start_version": 860,
    },
    "pm5": {
        "path": f"{THERMAL_PATH}/pm5",
        "default_value": 0.0,
        "start_version": 860,
    },
    "pm10": {
        "path": f"{THERMAL_PATH}/pm10",
        "default_value": 0.0,
        "start_version": 860,
    },
    "op1": {
        "path": f"{THERMAL_PATH}/op1",
        "default_value": 0.0,
        "start_version": 860,
    },
    "op2": {
        "path": f"{THERMAL_PATH}/op2",
        "default_value": 0.0,
        "start_version": 860,
    },
    "op3": {
        "path": f"{THERMAL_PATH}/op3",
        "default_value": 0.0,
        "start_version": 860,
    },
    "op4": {
        "path": f"{THERMAL_PATH}/op4",
        "default_value": 0.0,
        "start_version": 860,
    },
    "op5": {
        "path": f"{THERMAL_PATH}/op5",
        "default_value": 0.0,
        "start_version": 860,
    },
}


def format_path(path: str, area_id: str, cluster_id: str) -> str:
    return path.format(area=area_id, cluster=cluster_id)


class ThermalManager:
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_field_values(self, study: Study, area_id: str, cluster_id: str) -> ThermalFormFields:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        thermal_config = file_study.tree.get(format_path(THERMAL_PATH, area_id, cluster_id).split("/"))

        def get_value(field_info: FieldInfo) -> Any:
            target_name = PurePosixPath(field_info["path"]).name
            study_ver = file_study.config.version
            start_ver = cast(int, field_info.get("start_version", 0))
            end_ver = cast(int, field_info.get("end_version", study_ver))
            is_in_version = start_ver <= study_ver <= end_ver

            return thermal_config.get(target_name, field_info["default_value"]) if is_in_version else None

        return ThermalFormFields.construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

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
            execute_or_add_commands(study, file_study, commands, self.storage_service)
