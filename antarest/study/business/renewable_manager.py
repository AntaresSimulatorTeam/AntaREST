from enum import Enum
from pathlib import Path
from typing import Union, Optional, Dict, TypedDict, Any

from pydantic import StrictFloat, StrictInt, StrictStr, StrictBool

from antarest.study.business.utils import execute_or_add_commands, FormFieldsBaseModel
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class TsMode(str, Enum):
    PowerGeneration = "power-generation",
    ProductionFactor = "production-factor",


RENEWABLE_PATH = "input/renewables/clusters"


class RenewableFormFields(FormFieldsBaseModel):
    group: Optional[StrictStr]
    ts_mode: Optional[TsMode]
    name: Optional[StrictStr]
    unit_count: Optional[StrictInt]
    enabled: Optional[StrictBool]
    nominal_capacity: Optional[Union[StrictFloat, StrictInt]]


class FieldInfo(TypedDict, total=False):
    path: str
    default_value: Any


FIELDS_INFO: Dict[str, FieldInfo] = {
    "group": {
        "path": f"{RENEWABLE_PATH}/group",
        "default_value": "",
    },
    "ts_mode": {
        "path": f"{RENEWABLE_PATH}/ts-interpretation",
        "default_value": TsMode.PowerGeneration,
    },
    "name": {
        "path": f"{RENEWABLE_PATH}/name",
        "default_value": "",
    },
    "unit_count": {
        "path": f"{RENEWABLE_PATH}/unitcount",
        "default_value": 0,
    },
    "enabled": {
        "path": f"{RENEWABLE_PATH}/enabled",
        "default_value": True,
    },
    "nominal_capacity": {
        "path": f"{RENEWABLE_PATH}/nominalcapacity",
        "default_value": 0,
    }
}


class RenewableManager:
    def __init__(self, storage_service):
        self.storage_service = storage_service

    def get_field_values(self, study_id, area_id, cluster_id) -> RenewableFormFields:
        file_study = self.storage_service.get_storage(study_id).get_raw(study_id)
        renewable_config = file_study.tree.get([RENEWABLE_PATH, area_id, "list", cluster_id])

        def get_field_value(field_info: FieldInfo) -> Any:
            path = Path(field_info["path"]).parts[-1]
            return renewable_config.get(path, field_info["default_value"])

        return RenewableFormFields().construct(
            **{name: get_field_value(info) for name, info in FIELDS_INFO.items()}
        )

    def update_field_values(self, study_id, form_fields, area_id, cluster_id) -> None:
        commands = [
            UpdateConfig(
                target=[RENEWABLE_PATH, area_id, "list", cluster_id, Path(field_info['path']).parts[-1]],
                data=value,
                command_context=self.storage_service.variant_study_service.command_factory.command_context
            )
            for field_name, value in form_fields.dict(exclude_unset=True).items()
            if (field_info := FIELDS_INFO.get(field_name)) is not None
        ]

        if commands:
            file_study = self.storage_service.get_storage(study_id).get_raw(study_id)
            execute_or_add_commands(study_id, file_study, commands, self.storage_service)
