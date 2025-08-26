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

from pydantic.types import StrictBool, StrictFloat, StrictInt

from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext

DEFAULT_WEIGHT = 1


class PlaylistColumns(FormFieldsBaseModel):
    status: StrictBool
    weight: StrictFloat | StrictInt


class PlaylistManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_playlist(self, study: StudyInterface) -> dict[int, PlaylistColumns]:
        playlist = study.get_study_dao().get_playlist_config()
        args = playlist.model_dump()["years"]
        return {k: PlaylistColumns.model_validate(v) for k, v in args.items()}

    def update_playlist(self, study: StudyInterface, data: dict[int, PlaylistColumns]) -> None:
        years_by_bool: dict[bool, list[int]] = {True: [], False: []}
        for year, col in data.items():
            years_by_bool[col.status].append(year - 1)

        active_playlists = [year for year, col in data.items() if col.status is True]

        weights = {year: col.weight for year, col in data.items() if col.weight != DEFAULT_WEIGHT}

        command = UpdatePlaylist(
            items=active_playlists,
            weights=weights,
            active=True,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
