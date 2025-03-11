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

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import GENERAL_DATA_PATH
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TimeSeriesTypeConfig(AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True):
    number: int


@all_optional_model
class TimeSeriesConfigDTO(AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True):
    thermal: TimeSeriesTypeConfig


class TimeSeriesConfigManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_values(self, study: StudyInterface) -> TimeSeriesConfigDTO:
        """
        Get Time-Series generation values
        """
        file_study = study.get_files()
        url = GENERAL_DATA_PATH.split("/")
        url.extend(["general", "nbtimeseriesthermal"])
        nb_ts_gen_thermal = file_study.tree.get(url)

        args = {"thermal": TimeSeriesTypeConfig(number=nb_ts_gen_thermal)}
        return TimeSeriesConfigDTO.model_validate(args)

    def set_values(self, study: StudyInterface, field_values: TimeSeriesConfigDTO) -> None:
        """
        Set Time-Series generation values
        """

        if field_values.thermal:
            url = f"{GENERAL_DATA_PATH}/general/nbtimeseriesthermal"
            command = UpdateConfig(
                target=url,
                data=field_values.thermal.number,
                command_context=self._command_context,
                study_version=study.version,
            )
            study.add_commands([command])
