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
from typing import Any, Optional

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.link_model import LinkUpdate, update_link
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.link import parse_link_for_update
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(AbstractLinkCommand, ICommand):
    """
    Command used to update a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK

    # Command parameters
    # ==================

    parameters: LinkUpdate

    @model_validator(mode="before")
    @classmethod
    def _validate_parameters(cls, values: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        if "parameters" not in values:
            values["parameters"] = LinkUpdate()

        elif isinstance(values["parameters"], dict):
            parameters = values["parameters"]
            if info.context:
                version = info.context.version
                if version < 2:
                    parameters.pop("area1", None)
                    parameters.pop("area2", None)
                    values["parameters"] = parse_link_for_update(parameters)

        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_link = study_data.get_link(self.area1, self.area2)
        new_link = update_link(current_link, self.parameters)

        study_data.save_link(new_link)

        if self.series:
            study_data.save_link_series(self.area1, self.area2, str(self.series))

        if self.direct:
            study_data.save_link_direct_capacities(self.area1, self.area2, str(self.direct))

        if self.indirect:
            study_data.save_link_indirect_capacities(self.area1, self.area2, str(self.indirect))

        return command_succeeded(f"Link between '{self.area1}' and '{self.area2}' updated")

    @override
    def to_dto(self) -> CommandDTO:
        return super().command_to_dto(self.parameters, self.command_name)
