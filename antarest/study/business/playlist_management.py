# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from antarest.study.business.model.config.playlist_model import Playlist, PlaylistUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class PlaylistManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_playlist(self, study: StudyInterface) -> Playlist:
        return study.get_study_dao().get_playlist_config()

    def update_playlist(self, study: StudyInterface, playlist: PlaylistUpdate) -> Playlist:
        command = UpdatePlaylist(
            playlist=playlist,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return self.get_playlist(study)
