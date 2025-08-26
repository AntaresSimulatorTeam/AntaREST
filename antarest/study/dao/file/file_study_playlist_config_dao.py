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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import override

from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.dao.api.playlist_config_dao import PlaylistConfigDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyPlaylistConfigDao(PlaylistConfigDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_playlist_config(self) -> Playlist:
        config = self.get_file_study().tree.get(["settings", "generaldata"])
        playlist_config = config.get("playlist", {})

        # Reads the weights
        weights = {}
        for year_weight in playlist_config.get("playlist_year_weight", []):
            year_weight_elements = year_weight.split(",")
            weights[int(year_weight_elements[0])] = float(year_weight_elements[1])

        # Reads the years
        playlist = {}

        added = playlist_config.get("playlist_year +", [])
        for year in added:
            playlist[year + 1] = {"status": True, "weight": weights.get(year, 1)}

        removed = playlist_config.get("playlist_year -", [])
        for year in removed:
            playlist[year + 1] = {"status": False, "weight": weights.get(year, 1)}

        playlist_reset = playlist_config.get("playlist_reset", True)
        nb_years = self.get_impl().get_general_config().nb_years
        for year in range(nb_years):
            if year not in playlist:
                playlist[year] = {"status": playlist_reset, "weight": weights.get(year, 1)}

        # Build the object
        return Playlist(**playlist)

    @override
    def save_playlist_config(self, playlist: Playlist) -> None:
        raise NotImplementedError()
