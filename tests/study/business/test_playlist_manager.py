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
from typing import Any

import pytest

from antarest.study.business.model.config.playlist_model import Playlist, PlaylistValues
from antarest.study.business.playlist_management import PlaylistManager
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface


@pytest.mark.parametrize(
    ["general_data_content", "expected_playlist"],
    [
        (
            {"general": {"nbyears": 3}},
            Playlist(
                years={
                    1: PlaylistValues(status=True, weight=1),
                    2: PlaylistValues(status=True, weight=1),
                    3: PlaylistValues(status=True, weight=1),
                }
            ),
        ),
        (
            {
                "general": {"nbyears": 5},
                "playlist": {
                    "playlist_reset": False,
                    "playlist_year +": [1, 2],
                    "playlist_year_weight": ["1,5", "3,8"],
                },
            },
            Playlist(
                years={
                    1: PlaylistValues(status=False, weight=1),
                    2: PlaylistValues(status=True, weight=5.0),
                    3: PlaylistValues(status=True, weight=1),
                    4: PlaylistValues(status=False, weight=8.0),
                    5: PlaylistValues(status=False, weight=1),
                }
            ),
        ),
        (
            {
                "general": {"nbyears": 5},
                "playlist": {
                    "playlist_reset": True,
                    "playlist_year -": [1, 2],
                },
            },
            Playlist(
                years={
                    1: PlaylistValues(status=True, weight=1),
                    2: PlaylistValues(status=False, weight=1),
                    3: PlaylistValues(status=False, weight=1),
                    4: PlaylistValues(status=True, weight=1),
                    5: PlaylistValues(status=True, weight=1),
                }
            ),
        ),
    ],
)
def test_get_playlist(
    empty_study_880: FileStudy,
    general_data_content: dict[str, Any],
    expected_playlist: Playlist,
    command_context: CommandContext,
) -> None:
    empty_study_880.tree.save(general_data_content, ["settings", "generaldata"])
    manager = PlaylistManager(command_context)
    study = file_study_interface(empty_study_880)
    assert manager.get_playlist(study) == expected_playlist
