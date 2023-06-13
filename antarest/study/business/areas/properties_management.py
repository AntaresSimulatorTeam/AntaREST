import re
from builtins import sorted
from enum import Enum
from typing import Optional, Dict, Any, cast, List, Set, Iterable

from pydantic import root_validator, Field

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    FieldInfo,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)

AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas/{field}/{{area}}"
UI_PATH = f"{AREA_PATH}/ui/ui"
OPTIMIZATION_PATH = f"{AREA_PATH}/optimization"
NODAL_OPTIMIZATION_PATH = f"{OPTIMIZATION_PATH}/nodal optimization"
FILTERING_PATH = f"{OPTIMIZATION_PATH}/filtering"
# Keep the order
FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]
DEFAULT_FILTER_VALUE = FILTER_OPTIONS
DEFAULT_UI = {
    "color_r": 230,
    "color_g": 108,
    "color_b": 44,
}


def encode_color(ui: Dict[str, Any]) -> str:
    data = {**DEFAULT_UI, **ui}
    return f"{data['color_r']},{data['color_g']},{data['color_b']}"


def decode_color(
    encoded_color: str, current_ui: Optional[Dict[str, int]]
) -> Dict[str, Any]:
    r, g, b = map(int, encoded_color.split(","))
    return {**(current_ui or {}), "color_r": r, "color_g": g, "color_b": b}


def sort_filter_options(options: Iterable[str]) -> List[str]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def encode_filter(value: str) -> Set[str]:
    stripped = value.strip()
    return set(re.split(r"\s*,\s*", stripped) if stripped else [])


def decode_filter(
    encoded_value: Set[str], current_filter: Optional[str] = None
) -> str:
    return ", ".join(sort_filter_options(encoded_value))


class AdequacyPatchMode(str, Enum):
    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


class PropertiesFormFields(FormFieldsBaseModel):
    color: Optional[str] = Field(
        regex="^\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*$"
    )
    pos_x: Optional[float]
    pos_y: Optional[float]
    energy_cost_unsupplied: Optional[float]
    energy_cost_spilled: Optional[float]
    non_dispatch_power: Optional[bool]
    dispatch_hydro_power: Optional[bool]
    other_dispatch_power: Optional[bool]
    filter_synthesis: Optional[Set[str]]
    filter_by_year: Optional[Set[str]]
    # version 830
    adequacy_patch_mode: Optional[AdequacyPatchMode]

    @root_validator
    def validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        filters = {
            "filter_synthesis": values.get("filter_synthesis"),
            "filter_by_year": values.get("filter_by_year"),
        }
        for filter_name, val in filters.items():
            if val is not None:
                options = encode_filter(decode_filter(val))
                if any(opt not in FILTER_OPTIONS for opt in options):
                    raise ValueError(f"Invalid value in '{filter_name}'")

        return values


FIELDS_INFO: Dict[str, FieldInfo] = {
    # `color` must be before `pos_x` and `pos_y`, because they are include in the `decode_color`'s return dict value
    "color": {
        "path": UI_PATH,
        "encode": encode_color,
        "decode": decode_color,
        "default_value": encode_color(DEFAULT_UI),
    },
    "pos_x": {
        "path": f"{UI_PATH}/x",
        "default_value": 0.0,
    },
    "pos_y": {
        "path": f"{UI_PATH}/y",
        "default_value": 0.0,
    },
    "energy_cost_unsupplied": {
        "path": THERMAL_PATH.format(field="unserverdenergycost"),
        "default_value": 0.0,
    },
    "energy_cost_spilled": {
        "path": THERMAL_PATH.format(field="spilledenergycost"),
        "default_value": 0.0,
    },
    "non_dispatch_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/non-dispatchable-power",
        "default_value": True,
    },
    "dispatch_hydro_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/dispatchable-hydro-power",
        "default_value": True,
    },
    "other_dispatch_power": {
        "path": f"{NODAL_OPTIMIZATION_PATH}/other-dispatchable-power",
        "default_value": True,
    },
    "filter_synthesis": {
        "path": f"{FILTERING_PATH}/filter-synthesis",
        "encode": encode_filter,
        "decode": decode_filter,
        "default_value": DEFAULT_FILTER_VALUE,
    },
    "filter_by_year": {
        "path": f"{FILTERING_PATH}/filter-year-by-year",
        "encode": encode_filter,
        "decode": decode_filter,
        "default_value": DEFAULT_FILTER_VALUE,
    },
    "adequacy_patch_mode": {
        "path": f"{AREA_PATH}/adequacy_patch/adequacy-patch/adequacy-patch-mode",
        "default_value": AdequacyPatchMode.OUTSIDE.value,
        "start_version": 830,
    },
}


class PropertiesManager:
    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_field_values(
        self,
        study: Study,
        area_id: str,
    ) -> PropertiesFormFields:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        study_ver = file_study.config.version

        def get_value(field_info: FieldInfo) -> Any:
            start_ver = cast(int, field_info.get("start_version", 0))
            end_ver = cast(int, field_info.get("end_version", study_ver))
            is_in_version = start_ver <= study_ver <= end_ver
            if not is_in_version:
                return None

            try:
                val = file_study.tree.get(
                    field_info["path"].format(area=area_id).split("/")
                )
            except (ChildNotFoundError, KeyError):
                return field_info["default_value"]

            encode = field_info.get("encode") or (lambda x: x)
            return encode(val)

        return PropertiesFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self,
        study: Study,
        area_id: str,
        field_values: PropertiesFormFields,
    ) -> None:
        commands: List[UpdateConfig] = []
        file_study = self.storage_service.get_storage(study).get_raw(study)
        context = (
            self.storage_service.variant_study_service.command_factory.command_context
        )

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]
                decode = info.get("decode")
                target = info["path"].format(area=area_id)
                data = value

                if decode is not None:
                    try:
                        curr_value = file_study.tree.get(target.split("/"))
                    except (ChildNotFoundError, KeyError):
                        curr_value = None
                    data = decode(value, curr_value)

                commands.append(
                    UpdateConfig(
                        target=target,
                        data=data,
                        command_context=context,
                    )
                )

        if commands:
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )
