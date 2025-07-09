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

from typing import Dict, List, Union

from pydantic.types import StrictBool, StrictFloat, StrictInt

from antarest.study.business.model.config.general_model import FIELDS_INFO
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.variantstudy.model.command.update_playlist import UpdatePlaylist
from antarest.study.storage.variantstudy.model.command_context import CommandContext

DEFAULT_WEIGHT = 1


class PlaylistColumns(FormFieldsBaseModel):
    status: StrictBool
    weight: Union[StrictFloat, StrictInt]


class PlaylistManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_table_data(
        self,
        study: StudyInterface,
    ) -> Dict[int, PlaylistColumns]:
        file_study = study.get_files()
        playlist = FileStudyHelpers.get_playlist(file_study) or {}
        nb_years = file_study.tree.get(FIELDS_INFO["nb_years"]["path"].split("/")) or len(playlist)

        return {
            year: PlaylistColumns.model_construct(
                status=year in playlist,
                # TODO the real value for disable year
                weight=playlist.get(year, DEFAULT_WEIGHT),
            )
            for year in range(1, int(nb_years) + 1)  # type: ignore
        }

    def set_table_data(
        self,
        study: StudyInterface,
        data: Dict[int, PlaylistColumns],
    ) -> None:
        years_by_bool: Dict[bool, List[int]] = {True: [], False: []}
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
