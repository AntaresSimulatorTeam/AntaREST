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

from unittest.mock import Mock, call

from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


def test_set_playlist():
    study = Mock()
    study.tree.get.side_effect = [
        {
            "general": {"nbyears": 10, "user-playlist": True},
            "playlist": {"playlist_reset": True, "playlist_year -": [1, 2]},
        },
        {
            "general": {"nbyears": 10, "user-playlist": True},
            "playlist": {"playlist_reset": True, "playlist_year -": [1, 2]},
        },
        {"general": {"nbyears": 10, "user-playlist": False}},
        {"general": {"nbyears": 10, "user-playlist": False}},
    ]
    FileStudyHelpers.set_playlist(study, [2, 4])
    FileStudyHelpers.set_playlist(study, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    FileStudyHelpers.set_playlist(study, [2, 3, 4, 7, 8, 9])
    FileStudyHelpers.set_playlist(study, [2, 4], {2: 3})
    study.tree.save.assert_has_calls(
        [
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": False,
                        "playlist_year +": [1, 3],
                    },
                },
                ["settings", "generaldata"],
            ),
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": True,
                        "playlist_year -": [],
                    },
                },
                ["settings", "generaldata"],
            ),
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": True,
                        "playlist_year -": [0, 4, 5, 9],
                    },
                },
                ["settings", "generaldata"],
            ),
            call(
                {
                    "general": {"nbyears": 10, "user-playlist": True},
                    "playlist": {
                        "playlist_reset": False,
                        "playlist_year +": [1, 3],
                        "playlist_year_weight": ["1,3"],
                    },
                },
                ["settings", "generaldata"],
            ),
        ]
    )
