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

from typing import List, Optional

from pydantic import computed_field, field_validator
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.district_model import District, DistrictBaseFilter
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateDistrict(ICommand):
    """
    Command used to create a district in a study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_DISTRICT

    # Command parameters
    # ==================

    name: str
    base_filter: Optional[DistrictBaseFilter] = None
    areas: List[str] = []
    output: bool = True
    comments: str = ""

    @field_validator("name")
    def validate_district_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError("Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters")
        return val

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return transform_name_to_id(self.name)

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if study_data.district_exists(self.id):
            return command_failed(message=f"District '{self.name}' already exists and could not be created")

        new_district = District.model_validate(self.model_dump(include={"id", "name", "areas", "output", "comments"}))

        try:
            study_data.save_district(new_district, self.base_filter)
        except AreaNotFound as e:
            return command_failed(message=f"Area not found {e}")

        return command_succeeded(message=self.id)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args={
                "name": self.name,
                "base_filter": self.base_filter.value if self.base_filter else None,
                "areas": self.areas,
                "output": self.output,
                "comments": self.comments,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
