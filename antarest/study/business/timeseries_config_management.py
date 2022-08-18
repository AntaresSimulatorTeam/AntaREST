from enum import Enum
from typing import Dict, Optional, List

from pydantic import (
    root_validator,
    validator,
    StrictBool,
    StrictInt,
)

from antarest.core.model import JSON
from antarest.study.business.utils import (
    execute_or_add_commands,
    FormFieldsBaseModel,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class TSType(str, Enum):
    LOAD = "load"
    HYDRO = "hydro"
    THERMAL = "thermal"
    WIND = "wind"
    SOLAR = "solar"
    RENEWABLES = "renewables"
    NTC = "ntc"


class SeasonCorrelation(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class TSFormFieldsForType(FormFieldsBaseModel):
    stochastic_ts_status: Optional[StrictBool]
    number: Optional[StrictInt]
    refresh: Optional[StrictBool]
    refresh_interval: Optional[StrictInt]
    season_correlation: Optional[SeasonCorrelation]
    store_in_input: Optional[StrictBool]
    store_in_output: Optional[StrictBool]
    intra_modal: Optional[StrictBool]
    inter_modal: Optional[StrictBool]


class TSFormFields(FormFieldsBaseModel):
    load: Optional[TSFormFieldsForType] = None
    hydro: Optional[TSFormFieldsForType] = None
    thermal: Optional[TSFormFieldsForType] = None
    wind: Optional[TSFormFieldsForType] = None
    solar: Optional[TSFormFieldsForType] = None
    renewables: Optional[TSFormFieldsForType] = None
    ntc: Optional[TSFormFieldsForType] = None

    @root_validator(pre=True)
    def check_type_validity(
        cls, values: Dict[str, Optional[TSFormFieldsForType]]
    ) -> Dict[str, Optional[TSFormFieldsForType]]:
        def has_type(ts_type: TSType) -> bool:
            return values.get(ts_type.value, None) is not None

        if has_type(TSType.RENEWABLES) and (
            has_type(TSType.WIND) or has_type(TSType.SOLAR)
        ):
            raise ValueError(
                f"'{TSType.RENEWABLES}' type cannot be defined with '{TSType.WIND}' and '{TSType.SOLAR}' types"
            )
        return values

    @validator("thermal")
    def thermal_validation(cls, v: TSFormFieldsForType) -> TSFormFieldsForType:
        if v.season_correlation is not None:
            raise ValueError(
                "season_correlation is not allowed for 'thermal' type"
            )
        return v


GENERAL_DATA_PATH = "settings/generaldata"

PATH_BY_TS_STR_FIELD = {
    "stochastic_ts_status": f"{GENERAL_DATA_PATH}/general/generate",
    "refresh": f"{GENERAL_DATA_PATH}/general/refreshtimeseries",
    "intra_modal": f"{GENERAL_DATA_PATH}/general/intra-modal",
    "inter_modal": f"{GENERAL_DATA_PATH}/general/inter-modal",
    "store_in_input": f"{GENERAL_DATA_PATH}/input/import",
    "store_in_output": f"{GENERAL_DATA_PATH}/output/archives",
}


class TimeSeriesConfigManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_ts_field_values(self, study: Study) -> TSFormFields:
        """
        Get Time Series field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))

        fields = {
            ts_type.value: self.__get_form_fields_for_type(
                file_study,
                ts_type,
                general_data,
            )
            for ts_type in TSType
        }

        return TSFormFields.construct(**fields)

    def set_ts_field_values(
        self, study: Study, field_values: TSFormFields
    ) -> None:
        """
        Set Time Series config from the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)

        for ts_type, values in field_values:
            if values is not None:
                self.__set_ts_field_values_for_type(
                    study, file_study, TSType(ts_type), values
                )

    def __set_ts_field_values_for_type(
        self,
        study: Study,
        file_study: FileStudy,
        ts_type: TSType,
        field_values: TSFormFieldsForType,
    ) -> None:
        commands: List[UpdateConfig] = []
        values = field_values.dict()

        for field, path in PATH_BY_TS_STR_FIELD.items():
            field_val = values[field]
            if field_val is not None:
                commands.append(
                    self.__set_ts_types_str(
                        file_study, path, {ts_type: field_val}
                    )
                )

        if field_values.number is not None:
            commands.append(
                UpdateConfig(
                    target=f"{GENERAL_DATA_PATH}/general/nbtimeseries{ts_type}",
                    data=field_values.number,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            )

        if field_values.refresh_interval is not None:
            commands.append(
                UpdateConfig(
                    target=f"{GENERAL_DATA_PATH}/general/refreshinterval{ts_type}",
                    data=field_values.refresh_interval,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            )

        if field_values.season_correlation is not None:
            commands.append(
                UpdateConfig(
                    target=f"input/{ts_type}/prepro/correlation/general/mode",
                    data=field_values.season_correlation.value,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            )

        if len(commands) > 0:
            execute_or_add_commands(
                study, file_study, commands, self.storage_service
            )

    def __set_ts_types_str(
        self, file_study: FileStudy, path: str, values: Dict[TSType, bool]
    ) -> UpdateConfig:
        """
        Set string value with the format: "[ts_type_1], [ts_type_2]"
        """
        path_arr = path.split("/")

        try:
            parent_target = file_study.tree.get(path_arr[:-1])
        except:
            parent_target = {}

        target_value = parent_target.get(path_arr[-1], "")
        current_values = [v.strip() for v in target_value.split(",")]
        new_types = {
            **{
                ts_type: True
                for ts_type in TSType
                if ts_type in current_values
            },
            **values,
        }

        return UpdateConfig(
            target=path,
            data=", ".join(
                [ts_type for ts_type in new_types if new_types[ts_type]]
            ),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )

    @staticmethod
    def __has_ts_type_in_str(value: str, ts_type: TSType) -> bool:
        return ts_type in [v.strip() for v in value.split(",")]

    @staticmethod
    def __get_form_fields_for_type(
        file_study: FileStudy,
        ts_type: TSType,
        general_data: JSON,
    ) -> Optional[TSFormFieldsForType]:

        general = general_data.get("general", {})
        input_ = general_data.get("input", {})
        output = general_data.get("output", {})

        is_aggregated = (
            file_study.config.enr_modelling == ENR_MODELLING.AGGREGATED.value
        )

        if ts_type == TSType.RENEWABLES and is_aggregated:
            return None

        if ts_type in [TSType.WIND, TSType.SOLAR] and not is_aggregated:
            return None

        if ts_type == TSType.NTC and file_study.config.version < 820:
            return None

        is_special_type = ts_type == TSType.RENEWABLES or ts_type == TSType.NTC
        stochastic_ts_status = TimeSeriesConfigManager.__has_ts_type_in_str(
            general.get("generate", ""), ts_type
        )
        intra_modal = TimeSeriesConfigManager.__has_ts_type_in_str(
            general.get("intra-modal", ""), ts_type
        )
        inter_modal = TimeSeriesConfigManager.__has_ts_type_in_str(
            general.get("inter-modal", ""), ts_type
        )

        if is_special_type:
            return TSFormFieldsForType.construct(
                stochastic_ts_status=stochastic_ts_status,
                intra_modal=intra_modal,
                inter_modal=inter_modal
                if ts_type == TSType.RENEWABLES
                else None,
            )

        return TSFormFieldsForType.construct(
            stochastic_ts_status=stochastic_ts_status,
            number=general.get(f"nbtimeseries{ts_type}", 1),
            refresh=TimeSeriesConfigManager.__has_ts_type_in_str(
                general.get("refreshtimeseries", ""), ts_type
            ),
            refresh_interval=general.get(f"refreshinterval{ts_type}", 100),
            season_correlation=None
            if ts_type == TSType.THERMAL
            else file_study.tree.get(
                [
                    "input",
                    ts_type.value,
                    "prepro",
                    "correlation",
                    "general",
                    "mode",
                ]
            )
            or SeasonCorrelation.ANNUAL.value,
            store_in_input=TimeSeriesConfigManager.__has_ts_type_in_str(
                input_.get("import", ""), ts_type
            ),
            store_in_output=TimeSeriesConfigManager.__has_ts_type_in_str(
                output.get("archives", ""), ts_type
            ),
            intra_modal=intra_modal,
            inter_modal=inter_modal,
        )
