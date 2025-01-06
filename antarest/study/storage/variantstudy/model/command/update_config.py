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

import typing_extensions as te
from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_ENR_MODELLING_KEY = "settings/generaldata/other preferences/renewable-generation-modelling"

_Data: te.TypeAlias = t.Union[str, int, float, bool, JSON, None]


def _iter_dict(data: _Data, root_key: str = "") -> t.Generator[t.Tuple[str, t.Any], None, None]:
    if isinstance(data, dict):
        for key, value in data.items():
            sub_key = f"{root_key}/{key}" if root_key else key
            yield from _iter_dict(value, sub_key)
    else:
        yield root_key, data


class UpdateConfig(ICommand):
    """
    Command used to create a thermal cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_CONFIG
    version: int = 1

    # Command parameters
    # ==================

    target: str
    data: _Data

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        # The renewable-generation-modelling parameter must be reflected in the config
        if self.target.startswith("settings"):
            for key, value in _iter_dict(self.data, root_key=self.target):
                if key == _ENR_MODELLING_KEY:
                    study_data.enr_modelling = value
                    break

        return CommandOutput(status=True, message="ok"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(self.data, url)

        output, _ = self._apply_config(study_data.config)
        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args={
                "target": self.target,
                "data": self.data,
            },
            study_version=self.study_version,
        )

    @override
    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target)

    @override
    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateConfig):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.data == other.data

    @override
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return [other]

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []

    @override
    def can_update_study_config(self) -> bool:
        return False
