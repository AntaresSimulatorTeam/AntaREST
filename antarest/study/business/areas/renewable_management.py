from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

from pydantic import Field

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class TimeSeriesInterpretation(EnumIgnoreCase):
    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


RENEWABLE_PATH = "input/renewables/clusters/{area}/list/{cluster}"


class RenewableFormFields(FormFieldsBaseModel):
    """
    Pydantic model representing renewable cluster configuration form fields.
    """

    # fmt: off
    group: Optional[str]
    name: Optional[str]
    ts_interpretation: Optional[TimeSeriesInterpretation]
    unit_count: Optional[int] = Field(description="Unit count", ge=1)
    enabled: Optional[bool] = Field(description="Enable flag")
    nominal_capacity: Optional[float] = Field(description="Nominal capacity (MW)", ge=0)
    # fmt: on


FIELDS_INFO: Dict[str, FieldInfo] = {
    "group": {
        "path": f"{RENEWABLE_PATH}/group",
        "default_value": "",
    },
    "name": {
        "path": f"{RENEWABLE_PATH}/name",
        "default_value": "",
    },
    "ts_interpretation": {
        "path": f"{RENEWABLE_PATH}/ts-interpretation",
        "default_value": TimeSeriesInterpretation.POWER_GENERATION.value,
    },
    "unit_count": {
        "path": f"{RENEWABLE_PATH}/unitcount",
        "default_value": 1,
    },
    "enabled": {
        "path": f"{RENEWABLE_PATH}/enabled",
        "default_value": True,
    },
    "nominal_capacity": {
        "path": f"{RENEWABLE_PATH}/nominalcapacity",
        "default_value": 0,
    },
}


def format_path(path: str, area_id: str, cluster_id: str) -> str:
    return path.format(area=area_id, cluster=cluster_id)


class RenewableManager:
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_field_values(
        self, study: Study, area_id: str, cluster_id: str
    ) -> RenewableFormFields:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        renewable_config = file_study.tree.get(
            format_path(RENEWABLE_PATH, area_id, cluster_id).split("/")
        )

        def get_value(field_info: FieldInfo) -> Any:
            target_name = PurePosixPath(field_info["path"]).name
            return renewable_config.get(
                target_name, field_info["default_value"]
            )

        return RenewableFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        field_values: RenewableFormFields,
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
