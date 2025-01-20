# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.utils import GENERAL_DATA_PATH, FormFieldsBaseModel, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


@all_optional_model
class TSFormFields(FormFieldsBaseModel):
    thermal: int


class TimeSeriesConfigManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_values(self, study: Study) -> TSFormFields:
        """
        Get Time-Series generation values
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        url = GENERAL_DATA_PATH.split("/")
        url.extend(["general", "nbtimeseriesthermal"])
        nb_ts_gen_thermal = file_study.tree.get(url)

        args = {"thermal": nb_ts_gen_thermal}
        return TSFormFields.model_validate(args)

    def set_values(self, study: Study, field_values: TSFormFields) -> None:
        """
        Set Time-Series generation values
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)

        if field_values.thermal:
            url = f"{GENERAL_DATA_PATH}/general/nbtimeseriesthermal"
            command = UpdateConfig(
                target=url,
                data=field_values.thermal,
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
                study_version=file_study.config.version,
            )
            execute_or_add_commands(study, file_study, [command], self.storage_service)
