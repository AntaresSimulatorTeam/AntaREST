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

from typing import Any, Generator, List, Optional, Tuple

import typing_extensions as te
from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_ENR_MODELLING_KEY = "settings/generaldata/other preferences/renewable-generation-modelling"

_Data: te.TypeAlias = str | int | float | bool | JSON | None


def _iter_dict(data: _Data, root_key: str = "") -> Generator[Tuple[str, Any], None, None]:
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

    # Command parameters
    # ==================

    target: str
    data: _Data

    def update_in_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        # The renewable-generation-modelling parameter must be reflected in the config
        if self.target.startswith("settings"):
            for key, value in _iter_dict(self.data, root_key=self.target):
                if key == _ENR_MODELLING_KEY:
                    study_data.enr_modelling = value
                    break

        return CommandOutput(status=True, message="ok")

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(self.data, url)

        output = self.update_in_config(study_data.config)
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
    def get_inner_matrices(self) -> List[str]:
        return []
