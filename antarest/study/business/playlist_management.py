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


from antarest.study.business.model.config.playlist_model import PlaylistUpdate, PlaylistValues, PlaylistValuesUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class PlaylistManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_playlist(self, study: StudyInterface) -> dict[int, PlaylistValues]:
        return study.get_study_dao().get_playlist_config().years

    def update_playlist(
        self, study: StudyInterface, playlist: dict[int, PlaylistValuesUpdate]
    ) -> dict[int, PlaylistValues]:
        playlist_update = PlaylistUpdate.model_validate({"years": playlist})
        command = UpdatePlaylist(
            playlist=playlist_update,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return self.get_playlist(study)
