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

from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(AbstractLinkCommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK
    version: int = 1

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        area_from, area_to = sorted([self.area1, self.area2])

        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' updated",
            ),
            {"area_from": area_from, "area_to": area_to},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        version = study_data.config.version
        area_from, area_to = sorted([self.area1, self.area2])
        study_data.tree.save(self.parameters, ["input", "links", area_from, "properties", area_to])
        output, _ = self._apply_config(study_data.config)

        self.series = self.series or (self.command_context.generator_matrix_constants.get_link(version=version))
        self.direct = self.direct or (self.command_context.generator_matrix_constants.get_link_direct())
        self.indirect = self.indirect or (self.command_context.generator_matrix_constants.get_link_indirect())

        assert type(self.series) is str
        if version < STUDY_VERSION_8_2:
            study_data.tree.save(self.series, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(
                self.series,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )

            study_data.tree.save({}, ["input", "links", area_from, "capacities"])
            if self.direct:
                assert isinstance(self.direct, str)
                study_data.tree.save(
                    self.direct,
                    [
                        "input",
                        "links",
                        area_from,
                        "capacities",
                        f"{area_to}_direct",
                    ],
                )

            if self.indirect:
                assert isinstance(self.indirect, str)
                study_data.tree.save(
                    self.indirect,
                    [
                        "input",
                        "links",
                        area_from,
                        "capacities",
                        f"{area_to}_indirect",
                    ],
                )

        return output

    def to_dto(self) -> CommandDTO:
        args = {
            "area1": self.area1,
            "area2": self.area2,
            "parameters": self.parameters,
        }
        if self.series:
            args["series"] = strip_matrix_protocol(self.series)
        if self.direct:
            args["direct"] = strip_matrix_protocol(self.direct)
        if self.indirect:
            args["indirect"] = strip_matrix_protocol(self.indirect)
        return CommandDTO(
            action=CommandName.UPDATE_LINK.value,
            args=args,
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.area1 + MATCH_SIGNATURE_SEPARATOR + self.area2
        )

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return super()._create_diff(other)

    def get_inner_matrices(self) -> t.List[str]:
        return super().get_inner_matrices()
