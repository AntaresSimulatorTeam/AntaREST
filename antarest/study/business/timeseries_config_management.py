# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import typing as t

from pydantic import StrictBool, StrictInt, field_validator, model_validator

from antarest.core.model import JSON
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.utils import GENERAL_DATA_PATH, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class TSType(EnumIgnoreCase):
    LOAD = "load"
    HYDRO = "hydro"
    THERMAL = "thermal"
    WIND = "wind"
    SOLAR = "solar"
    RENEWABLES = "renewables"
    NTC = "ntc"


class SeasonCorrelation(EnumIgnoreCase):
    MONTHLY = "monthly"
    ANNUAL = "annual"


@all_optional_model
class TSFormFieldsForType(FormFieldsBaseModel):
    stochastic_ts_status: StrictBool
    number: StrictInt
    refresh: StrictBool
    refresh_interval: StrictInt
    season_correlation: SeasonCorrelation
    store_in_input: StrictBool
    store_in_output: StrictBool
    intra_modal: StrictBool
    inter_modal: StrictBool


@all_optional_model
class TSFormFields(FormFieldsBaseModel):
    load: TSFormFieldsForType
    hydro: TSFormFieldsForType
    thermal: TSFormFieldsForType
    wind: TSFormFieldsForType
    solar: TSFormFieldsForType
    renewables: TSFormFieldsForType
    ntc: TSFormFieldsForType

    @model_validator(mode="before")
    def check_type_validity(
        cls, values: t.Dict[str, t.Optional[TSFormFieldsForType]]
    ) -> t.Dict[str, t.Optional[TSFormFieldsForType]]:
        def has_type(ts_type: TSType) -> bool:
            return values.get(ts_type.value, None) is not None

        if has_type(TSType.RENEWABLES) and (has_type(TSType.WIND) or has_type(TSType.SOLAR)):
            raise ValueError(
                f"'{TSType.RENEWABLES}' type cannot be defined with '{TSType.WIND}' and '{TSType.SOLAR}' types"
            )
        return values

    @field_validator("thermal")
    def thermal_validation(cls, v: TSFormFieldsForType) -> TSFormFieldsForType:
        if v.season_correlation is not None:
            raise ValueError("season_correlation is not allowed for 'thermal' type")
        return v


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

    def get_field_values(self, study: Study) -> TSFormFields:
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

        return TSFormFields.construct(**fields)  # type: ignore

    def set_field_values(self, study: Study, field_values: TSFormFields) -> None:
        """
        Set Time Series config from the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)

        for ts_type, values in field_values:
            if values is not None:
                self.__set_field_values_for_type(study, file_study, TSType(ts_type), values)

    def __set_field_values_for_type(
        self,
        study: Study,
        file_study: FileStudy,
        ts_type: TSType,
        field_values: TSFormFieldsForType,
    ) -> None:
        commands: t.List[UpdateConfig] = []
        values = field_values.model_dump()

        for field, path in PATH_BY_TS_STR_FIELD.items():
            field_val = values[field]
            if field_val is not None:
                commands.append(self.__set_ts_types_str(file_study, path, {ts_type: field_val}))

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
            execute_or_add_commands(study, file_study, commands, self.storage_service)

    def __set_ts_types_str(self, file_study: FileStudy, path: str, values: t.Dict[TSType, bool]) -> UpdateConfig:
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
            **{ts_type: True for ts_type in TSType if ts_type in current_values},
            **values,
        }

        return UpdateConfig(
            target=path,
            data=", ".join([ts_type for ts_type in new_types if new_types[ts_type]]),
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
    ) -> t.Optional[TSFormFieldsForType]:
        general = general_data.get("general", {})
        input_ = general_data.get("input", {})
        output = general_data.get("output", {})

        config = file_study.config
        study_version = config.version
        has_renewables = study_version >= 810 and EnrModelling(config.enr_modelling) == EnrModelling.CLUSTERS

        if ts_type == TSType.RENEWABLES and not has_renewables:
            return None

        if ts_type in [TSType.WIND, TSType.SOLAR] and has_renewables:
            return None

        if ts_type == TSType.NTC and study_version < 820:
            return None

        is_special_type = ts_type == TSType.RENEWABLES or ts_type == TSType.NTC
        stochastic_ts_status = TimeSeriesConfigManager.__has_ts_type_in_str(general.get("generate", ""), ts_type)
        intra_modal = TimeSeriesConfigManager.__has_ts_type_in_str(general.get("intra-modal", ""), ts_type)
        inter_modal = TimeSeriesConfigManager.__has_ts_type_in_str(general.get("inter-modal", ""), ts_type)

        if is_special_type:
            return TSFormFieldsForType.construct(
                stochastic_ts_status=stochastic_ts_status,
                intra_modal=intra_modal,
                inter_modal=inter_modal if ts_type == TSType.RENEWABLES else None,
            )

        return TSFormFieldsForType.construct(
            stochastic_ts_status=stochastic_ts_status,
            number=general.get(f"nbtimeseries{ts_type}", 1),
            refresh=TimeSeriesConfigManager.__has_ts_type_in_str(general.get("refreshtimeseries", ""), ts_type),
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
            or SeasonCorrelation.ANNUAL,
            store_in_input=TimeSeriesConfigManager.__has_ts_type_in_str(input_.get("import", ""), ts_type),
            store_in_output=TimeSeriesConfigManager.__has_ts_type_in_str(output.get("archives", ""), ts_type),
            intra_modal=intra_modal,
            inter_modal=inter_modal,
        )
