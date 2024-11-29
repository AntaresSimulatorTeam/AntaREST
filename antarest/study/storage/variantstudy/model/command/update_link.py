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

from antarest.study.business.model.link_model import LinkInternal
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(AbstractLinkCommand):
    """
    Command used to update a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK
    version: int = 1

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' updated",
            ),
            {},
        )

    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        version = study_data.config.version

        properties = study_data.tree.get(["input", "links", self.area1, "properties", self.area2])

        new_properties = LinkInternal.model_validate(self.parameters).model_dump(include=self.parameters, by_alias=True)

        properties.update(new_properties)

        study_data.tree.save(properties, ["input", "links", self.area1, "properties", self.area2])

        output, _ = self._apply_config(study_data.config)

        if self.series:
            self.save_series(self.area1, self.area2, study_data, version)

        if self.direct:
            self.save_direct(self.area1, self.area2, study_data, version)

        if self.indirect:
            self.save_indirect(self.area1, self.area2, study_data, version)

        return output

    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    def match_signature(self) -> str:
        return super().match_signature()

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return super()._create_diff(other)

    def get_inner_matrices(self) -> t.List[str]:
        return super().get_inner_matrices()
