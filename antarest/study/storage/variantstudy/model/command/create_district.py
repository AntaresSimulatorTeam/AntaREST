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
from dataclasses import dataclass
from typing import Any, Dict, Final, Optional

from pydantic import ValidationInfo, field_validator, model_validator
from typing_extensions import override

from antarest.study.business.model.district_model import District, DistrictCreation, create_district
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.common import (
    CommandApplicationResult,
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


@dataclass(frozen=True)
class CreateDistrictResult(CommandApplicationResult):
    data: District


class CreateDistrict(ICommand):
    """
    Command used to create a district in a study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_DISTRICT

    # Command parameters
    # ==================

    parameters: DistrictCreation

    # version 2: rename filter_items to areas, move all parameters under "parameters"
    _SERIALIZATION_VERSION: Final[int] = 2

    @model_validator(mode="before")
    @classmethod
    def _migrate_v1_to_v2(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                parameters = {}
                if "name" in values:
                    parameters["name"] = values.pop("name")
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

    @field_validator("parameters")
    def validate_district_name(cls, val: DistrictCreation) -> DistrictCreation:
        valid_name = transform_name_to_id(val.name, lower=False)
        if valid_name != val.name:
            raise ValueError("Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters")
        return val

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        district_id = transform_name_to_id(self.parameters.name)

        if study_data.district_exists(district_id):
            return command_failed(message=f"District '{self.parameters.name}' already exists and could not be created")

        invalid_areas = study_data.get_invalid_area_ids(self.parameters.areas or [])
        if invalid_areas:
            return command_failed(message=f"District '{self.parameters.name}' has invalid areas: {invalid_areas}")

        new_district_definition = create_district(self.parameters, district_id)

        study_data.save_district(new_district_definition)

        result = CreateDistrictResult(data=new_district_definition)
        return command_succeeded(message=district_id, result=result)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args={
                "parameters": self.parameters.model_dump(mode="json", exclude_none=True),
            },
            version=self._SERIALIZATION_VERSION,
            study_version=self.study_version,
        )
