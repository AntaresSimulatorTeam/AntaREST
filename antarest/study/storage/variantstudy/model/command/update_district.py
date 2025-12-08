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

from typing import Any, Dict, Final, Optional

from pydantic import ValidationInfo, model_validator
from typing_extensions import override

from antarest.study.business.model.district_model import DistrictUpdate, update_district
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateDistrict(ICommand):
    """
    Command used to update a district in a study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_DISTRICT

    # Command parameters
    # ==================

    id: str

    parameters: DistrictUpdate
    # version 2: rename filter_items to areas, move all parameters under "parameters"
    _SERIALIZATION_VERSION: Final[int] = 2

    @model_validator(mode="before")
    @classmethod
    def _migrate_v1_to_v2(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                parameters = {}
                if "base_filter" in values:
                    parameters["apply_filter"] = values.pop("base_filter")
                if "filter_items" in values:
                    parameters["areas"] = values.pop("filter_items")
                if "output" in values:
                    parameters["output"] = values.pop("output")
                if "comments" in values:
                    parameters["comments"] = values.pop("comments")
                values["parameters"] = parameters
        return values

    class Config:
        populate_by_name = True

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.district_exists(self.id):
            return command_failed(message=f"District '{self.id}' does not exist and should be created")

        invalid_areas = study_data.get_invalid_areas_in_district(self.parameters.areas or [])
        if invalid_areas:
            return command_failed(message=f"District '{self.id}' has invalid areas: {invalid_areas}")

        district = study_data.get_district(self.id)

        updated_district = update_district(district, self.parameters)

        study_data.save_district(updated_district)

        return command_succeeded(message=self.id)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args={
                "id": self.id,
                "parameters": self.parameters.model_dump(mode="json", exclude_none=True),
            },
            version=self._SERIALIZATION_VERSION,
            study_version=self.study_version,
        )
