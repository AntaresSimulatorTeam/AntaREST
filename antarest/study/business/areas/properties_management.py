import re
import typing as t
from builtins import sorted

from pydantic import root_validator

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.utils import FieldInfo, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.area import AdequacyPatchMode
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

AREA_PATH = "input/areas/{area}"
THERMAL_PATH = "input/thermal/areas/{field}/{{area}}"
OPTIMIZATION_PATH = f"{AREA_PATH}/optimization"
NODAL_OPTIMIZATION_PATH = f"{OPTIMIZATION_PATH}/nodal optimization"
FILTERING_PATH = f"{OPTIMIZATION_PATH}/filtering"
# Keep the order
FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]
DEFAULT_FILTER_VALUE = FILTER_OPTIONS


def sort_filter_options(options: t.Iterable[str]) -> t.List[str]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def encode_filter(value: str) -> t.Set[str]:
    stripped = value.strip()
    return set(re.split(r"\s*,\s*", stripped) if stripped else [])


def decode_filter(encoded_value: t.Set[str], current_filter: t.Optional[str] = None) -> str:
    return ", ".join(sort_filter_options(encoded_value))


class PropertiesFormFields(FormFieldsBaseModel):
    energy_cost_unsupplied: t.Optional[float]
    energy_cost_spilled: t.Optional[float]
    non_dispatch_power: t.Optional[bool]
    dispatch_hydro_power: t.Optional[bool]
    other_dispatch_power: t.Optional[bool]
    filter_synthesis: t.Optional[t.Set[str]]
    filter_by_year: t.Optional[t.Set[str]]
    # version 830
    adequacy_patch_mode: t.Optional[AdequacyPatchMode]

    @root_validator
    def validation(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
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


FIELDS_INFO: t.Dict[str, FieldInfo] = {
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

        def get_value(field_info: FieldInfo) -> t.Any:
            start_ver = t.cast(int, field_info.get("start_version", 0))
            end_ver = t.cast(int, field_info.get("end_version", study_ver))
            is_in_version = start_ver <= study_ver <= end_ver
            if not is_in_version:
                return None

            try:
                val = file_study.tree.get(field_info["path"].format(area=area_id).split("/"))
            except (ChildNotFoundError, KeyError):
                return field_info["default_value"]

            encode = field_info.get("encode") or (lambda x: x)
            return encode(val)

        return PropertiesFormFields.construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(
        self,
        study: Study,
        area_id: str,
        field_values: PropertiesFormFields,
    ) -> None:
        commands: t.List[UpdateConfig] = []
        file_study = self.storage_service.get_storage(study).get_raw(study)
        context = self.storage_service.variant_study_service.command_factory.command_context

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
            execute_or_add_commands(study, file_study, commands, self.storage_service)
