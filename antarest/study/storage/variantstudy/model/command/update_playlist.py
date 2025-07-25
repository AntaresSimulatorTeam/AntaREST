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

from typing import Dict, List, Optional

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdatePlaylist(ICommand):
    """
    Command used to update a playlist.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_PLAYLIST

    # Command parameters
    # ==================

    active: bool
    items: Optional[List[int]] = None
    weights: Optional[Dict[int, float]] = None
    reverse: bool = False

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        FileStudyHelpers.set_playlist(
            study_data,
            self.items or [],
            self.weights,
            reverse=self.reverse,
            active=self.active,
        )
        return command_succeeded("Playlist has been updated successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_PLAYLIST.value,
            args={
                "active": self.active,
                "items": self.items,
                "weights": self.weights,
                "reverse": self.reverse,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
