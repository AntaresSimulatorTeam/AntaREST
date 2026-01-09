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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

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
            if year + 1 not in playlist:
                playlist[year + 1] = {"status": playlist_reset, "weight": weights.get(year, 1)}

        # Build the object
        return Playlist.model_validate({"years": playlist})

    @override
    def save_playlist_config(self, playlist: Playlist) -> None:
        activated_years = []
        deactivated_years = []
        weights = []
        for year, model in playlist.years.items():
            ini_year = year - 1
            if model.status:
                activated_years.append(ini_year)
            else:
                deactivated_years.append(ini_year)
            if model.weight != 1:
                # Only write weights if they differ from the default value
                weights.append(f"{ini_year},{model.weight}")

        content: dict[str, Any] = {"playlist_year_weight": weights}

        all_years = len(playlist.years)
        # Determine what's lighter to write inside the file
        if len(activated_years) > all_years // 2:
            # Means we'll write only deactivated years
            content["playlist_reset"] = True
            content["playlist_year -"] = deactivated_years
        else:
            # Means we'll write only activated years
            content["playlist_reset"] = False
            content["playlist_year +"] = activated_years

        self.get_file_study().tree.save(content, ["settings", "generaldata", "playlist"])
