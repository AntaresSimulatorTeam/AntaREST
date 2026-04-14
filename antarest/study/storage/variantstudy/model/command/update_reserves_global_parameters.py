# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserves_global_parameters_model import (
    ReservesGlobalParameters,
    ReservesGlobalParametersUpdate,
    update_reserves_global_parameters,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateReservesGlobalParameters(ICommand):
    """
    Command used to update the reserves global parameters for multiple areas.
    """

    command_name: CommandName = CommandName.UPDATE_RESERVES_GLOBAL_PARAMETERS

    properties: dict[str, ReservesGlobalParametersUpdate]

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError("Reserves global parameters are not valid for study version before 10.0")
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[dict[str, ReservesGlobalParameters]]:
        all_area_ids = study_data.get_all_area_ids()
        invalid_areas = [area_id for area_id in self.properties if area_id not in all_area_ids]
        if invalid_areas:
            return command_failed(f"Areas do not exist: {', '.join(invalid_areas)}")

        new_params_mapping: dict[str, ReservesGlobalParameters] = {}
        for area_id, update in self.properties.items():
            current = study_data.get_reserves_global_parameters(area_id)
            new_params_mapping[area_id] = update_reserves_global_parameters(current, update)

        study_data.save_reserves_global_parameters(new_params_mapping)

        message = f"Reserves global parameters updated for areas: {', '.join(self.properties.keys())}"
        return command_succeeded(message=message, result=new_params_mapping)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "properties": {
                    area_id: params.model_dump(mode="json", exclude_none=True)
                    for area_id, params in self.properties.items()
                },
            },
            study_version=self.study_version,
        )
