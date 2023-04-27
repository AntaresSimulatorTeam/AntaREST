from enum import Enum
from typing import Optional, Dict, Any, List, cast

from pydantic import StrictBool, conint, PositiveInt, root_validator

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    FieldInfo,
    GENERAL_DATA_PATH,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class Mode(str, Enum):
    ECONOMY = "Economy"
    ADEQUACY = "Adequacy"
    DRAFT = "draft"


class Month(str, Enum):
    JANUARY = "january"
    FEBRUARY = "february"
    MARCH = "march"
    APRIL = "april"
    MAY = "may"
    JUNE = "june"
    JULY = "july"
    AUGUST = "august"
    SEPTEMBER = "september"
    OCTOBER = "october"
    NOVEMBER = "november"
    DECEMBER = "december"


class WeekDay(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class BuildingMode(str, Enum):
    AUTOMATIC = "Automatic"
    CUSTOM = "Custom"
    DERATED = "Derated"


DayNumberType = conint(ge=1, le=366)


class GeneralFormFields(FormFieldsBaseModel):
    mode: Optional[Mode]
    first_day: Optional[DayNumberType]  # type: ignore
    last_day: Optional[DayNumberType]  # type: ignore
    horizon: Optional[str]  # Don't use `StrictStr` because it can be an int
    first_month: Optional[Month]
    first_week_day: Optional[WeekDay]
    first_january: Optional[WeekDay]
    leap_year: Optional[StrictBool]
    nb_years: Optional[PositiveInt]
    building_mode: Optional[BuildingMode]
    selection_mode: Optional[StrictBool]
    year_by_year: Optional[StrictBool]
    simulation_synthesis: Optional[StrictBool]
    mc_scenario: Optional[StrictBool]
    # Geographic trimming + Thematic trimming.
    # For study versions < 710
    filtering: Optional[StrictBool]
    # For study versions >= 710
    geographic_trimming: Optional[StrictBool]
    thematic_trimming: Optional[StrictBool]

    @root_validator
    def day_fields_validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        first_day = values.get("first_day")
        last_day = values.get("last_day")
        leap_year = values.get("leap_year")

        if any(v is None for v in [first_day, last_day, leap_year]):
            raise ValueError(
                "First day, last day and leap year fields must be defined together"
            )

        first_day = cast(int, first_day)
        last_day = cast(int, last_day)
        leap_year = cast(bool, leap_year)
        num_days_in_year = 366 if leap_year else 365

        if first_day > last_day:
            raise ValueError(
                "Last day must be greater than or equal to the first day"
            )
        if last_day > num_days_in_year:
            raise ValueError(
                f"Last day cannot be greater than {num_days_in_year}"
            )

        return values


GENERAL = "general"
OUTPUT = "output"
GENERAL_PATH = f"{GENERAL_DATA_PATH}/{GENERAL}"
OUTPUT_PATH = f"{GENERAL_DATA_PATH}/{OUTPUT}"
BUILDING_MODE = "building_mode"


FIELDS_INFO: Dict[str, FieldInfo] = {
    "mode": {
        "path": f"{GENERAL_PATH}/mode",
        "default_value": Mode.ECONOMY.value,
    },
    "first_day": {
        "path": f"{GENERAL_PATH}/simulation.start",
        "default_value": 1,
    },
    "last_day": {
        "path": f"{GENERAL_PATH}/simulation.end",
        "default_value": 365,
    },
    "horizon": {
        "path": f"{GENERAL_PATH}/horizon",
        "default_value": "",
    },
    "first_month": {
        "path": f"{GENERAL_PATH}/first-month-in-year",
        "default_value": Month.JANUARY.value,
    },
    "first_week_day": {
        "path": f"{GENERAL_PATH}/first.weekday",
        "default_value": WeekDay.MONDAY.value,
    },
    "first_january": {
        "path": f"{GENERAL_PATH}/january.1st",
        "default_value": WeekDay.MONDAY.value,
    },
    "leap_year": {
        "path": f"{GENERAL_PATH}/leapyear",
        "default_value": False,
    },
    "nb_years": {
        "path": f"{GENERAL_PATH}/nbyears",
        "default_value": 1,
    },
    BUILDING_MODE: {
        "path": "",
        "default_value": BuildingMode.AUTOMATIC.value,
    },
    "selection_mode": {
        "path": f"{GENERAL_PATH}/user-playlist",
        "default_value": False,
    },
    "year_by_year": {
        "path": f"{GENERAL_PATH}/year-by-year",
        "default_value": False,
    },
    "filtering": {
        "path": f"{GENERAL_PATH}/filtering",
        "default_value": False,
        "end_version": 700,
    },
    "geographic_trimming": {
        "path": f"{GENERAL_PATH}/geographic-trimming",
        "default_value": False,
        "start_version": 710,
    },
    "thematic_trimming": {
        "path": f"{GENERAL_PATH}/thematic-trimming",
        "default_value": False,
        "start_version": 710,
    },
    "simulation_synthesis": {
        "path": f"{OUTPUT_PATH}/synthesis",
        "default_value": True,
    },
    "mc_scenario": {
        "path": f"{OUTPUT_PATH}/storenewset",
        "default_value": False,
    },
}


class GeneralManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> GeneralFormFields:
        """
        Get General field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        general = general_data.get(GENERAL, {})
        output = general_data.get(OUTPUT, {})

        def get_value(field_name: str, field_info: FieldInfo) -> Any:
            if field_name == BUILDING_MODE:
                return GeneralManager.__get_building_mode_value(general)

            path = field_info["path"]
            study_ver = file_study.config.version
            start_ver = field_info.get("start_version", -1)
            end_ver = field_info.get("end_version", study_ver)
            target_name = path.split("/")[-1]
            is_in_version = start_ver <= study_ver <= end_ver  # type: ignore
            parent = general if GENERAL_PATH in path else output

            return (
                parent.get(target_name, field_info["default_value"])
                if is_in_version
                else None
            )

        return GeneralFormFields.construct(
            **{
                name: get_value(name, info)
                for name, info in FIELDS_INFO.items()
            }
        )

    def set_field_values(
        self, study: Study, field_values: GeneralFormFields
    ) -> None:
        """
        Set Optimization config from the webapp form
        """
        commands: List[UpdateConfig] = []
        cmd_cx = (
            self.storage_service.variant_study_service.command_factory.command_context
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                if field_name == BUILDING_MODE:
                    commands.extend(
                        GeneralManager.__get_building_mode_update_cmds(
                            value, file_study, cmd_cx
                        )
                    )
                    continue

                commands.append(
                    UpdateConfig(
                        target=info["path"], data=value, command_context=cmd_cx
                    )
                )

        if len(commands) > 0:
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )

    @staticmethod
    def __get_building_mode_value(general_config: Dict[str, Any]) -> str:
        if general_config.get("derated", False):
            return BuildingMode.DERATED.value

        # 'custom-scenario' replaces 'custom-ts-numbers' in study versions >= 800
        if general_config.get("custom-scenario", False) or general_config.get(
            "custom-ts-numbers", False
        ):
            return BuildingMode.CUSTOM.value

        return str(FIELDS_INFO[BUILDING_MODE]["default_value"])

    @staticmethod
    def __get_building_mode_update_cmds(
        new_value: BuildingMode,
        file_study: FileStudy,
        cmd_context: CommandContext,
    ) -> List[UpdateConfig]:
        if new_value == BuildingMode.DERATED:
            return [
                UpdateConfig(
                    target=f"{GENERAL_PATH}/derated",
                    data=True,
                    command_context=cmd_context,
                )
            ]

        return [
            UpdateConfig(
                target=f"{GENERAL_PATH}/custom-scenario"
                if file_study.config.version >= 800
                else f"{GENERAL_PATH}/custom-ts-numbers",
                data=new_value == BuildingMode.CUSTOM,
                command_context=cmd_context,
            ),
            UpdateConfig(
                target=f"{GENERAL_PATH}/derated",
                data=False,
                command_context=cmd_context,
            ),
        ]
