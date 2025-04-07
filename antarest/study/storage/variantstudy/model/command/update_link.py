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

from typing_extensions import override

from antarest.study.business.model.link_model import LinkInternal
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(AbstractLinkCommand):
    """
    Command used to update a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        version = study_data.config.version

        properties = study_data.tree.get(["input", "links", self.area1, "properties", self.area2])

        new_properties = LinkInternal.model_validate(self.parameters).model_dump(include=self.parameters, by_alias=True)

        properties.update(new_properties)

        study_data.tree.save(properties, ["input", "links", self.area1, "properties", self.area2])

        if self.series:
            self.save_series(self.area1, self.area2, study_data, version)

        if self.direct:
            self.save_direct(self.area1, self.area2, study_data, version)

        if self.indirect:
            self.save_indirect(self.area1, self.area2, study_data, version)

        return CommandOutput(
            status=True,
            message=f"Link between '{self.area1}' and '{self.area2}' updated",
        )

    @override
    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    @override
    def get_inner_matrices(self) -> List[str]:
        return super().get_inner_matrices()
