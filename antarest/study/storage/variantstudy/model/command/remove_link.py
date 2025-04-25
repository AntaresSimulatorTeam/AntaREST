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

from pydantic import field_validator, model_validator
from typing_extensions import override

from antarest.study.business.model.link_model import Link
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


class RemoveLink(ICommand):
    """
    Command used to remove a link.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_LINK

    # Command parameters
    # ==================

    # Properties of the `REMOVE_LINK` command:
    area1: str
    area2: str

    # noinspection PyMethodParameters
    @field_validator("area1", "area2", mode="before")
    def _validate_id(cls, area: str) -> str:
        if isinstance(area, str):
            # Area IDs must be in lowercase and not empty.
            area_id = transform_name_to_id(area, lower=True)
            if area_id:
                return area_id
            # Valid characters are `[a-zA-Z0-9_(),& -]` (including space).
            raise ValueError(f"Invalid area '{area}': it must not be empty or contain invalid characters")

        # Delegates the validation to Pydantic validators (e.g: type checking).
        return area

    # noinspection PyMethodParameters
    @model_validator(mode="after")
    def _validate_link(self) -> "RemoveLink":
        # By convention, the source area is always the smallest one (in lexicographic order).
        if self.area1 > self.area2:
            self.area1, self.area2 = self.area2, self.area1
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.link_exists(self.area1, self.area2):
            return command_failed(f"Link between '{self.area1}' and '{self.area2}' doesn't exists")

        study_data.delete_link(Link(**{"area1": self.area1, "area2": self.area2}))

        return command_succeeded(f"Link between '{self.area1}' and '{self.area2}' deleted")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args={"area1": self.area1, "area2": self.area2},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
