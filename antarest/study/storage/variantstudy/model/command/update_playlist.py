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

from typing import Any, Dict, Final, Optional

from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.study.business.model.config.playlist_model import PlaylistUpdate, update_playlist
from antarest.study.dao.api.study_dao import StudyDao
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

    # version 2: changes from legacy representation to PlaylistUpdate class
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    playlist: PlaylistUpdate

    @model_validator(mode="before")
    @classmethod
    def _migrate_v1_to_v2(cls, values: dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                playlist = {}
                years = values.pop("items")
                weights = values.pop("weights")
                for year in years:
                    playlist[year] = {"status": True, "weight": weights.get(year)}
                for year, weight in weights.items():
                    if year in playlist:
                        playlist[year]["weight"] = weight
                    else:
                        playlist[year] = {"weight": weight}
                values.pop("active")
                values.pop("reverse")
                values["playlist"] = {"years": playlist}

        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_config = study_data.get_playlist_config()
        new_playlist = update_playlist(current_config, self.playlist)
        study_data.save_playlist_config(new_playlist)
        return command_succeeded("Playlist has been updated successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_PLAYLIST.value,
            version=self._SERIALIZATION_VERSION,
            args={"playlist": self.playlist.model_dump(exclude_none=True)},
            study_version=self.study_version,
        )
