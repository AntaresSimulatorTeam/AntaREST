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

from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ConfigManager:
    def __init__(
        self,
        command_context: CommandContext,
    ) -> None:
        self._command_context = command_context

    def get_playlist(self, study: StudyInterface) -> Optional[Dict[int, float]]:
        return FileStudyHelpers.get_playlist(study.get_files())

    def set_playlist(
        self,
        study: StudyInterface,
        playlist: Optional[List[int]],
        weights: Optional[Dict[int, int]],
        reverse: bool,
        active: bool,
    ) -> None:
        command = UpdatePlaylist(
            items=playlist,
            weights=weights,
            reverse=reverse,
            active=active,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
