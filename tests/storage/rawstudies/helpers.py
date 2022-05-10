from unittest.mock import Mock, call

import pytest

from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers


@pytest.mark.parametrize(
    ["generaldata", "playlist"],
    [
        (
            {"general": {"nbyears": 10, "user-playlist": False}},
            None,
        ),
        (
            {"general": {"nbyears": 10, "user-playlist": True}},
            list(range(1, 11)),
        ),
        (
            {
                "general": {"nbyears": 10, "user-playlist": False},
                "playlist": {
                    "playlist_reset": False,
                    "playlist_year +": [1, 2],
                },
            },
            None,
        ),
        (
            {
                "general": {"nbyears": 10, "user-playlist": True},
                "playlist": {
                    "playlist_reset": False,
                    "playlist_year +": [1, 2],
                },
            },
            [2, 3],
        ),
        (
            {
                "general": {"nbyears": 10, "user-playlist": True},
                "playlist": {
                    "playlist_reset": True,
                    "playlist_year -": [1, 2],
                },
            },
            [1, 4, 5, 6, 7, 8, 9, 10],
        ),
    ],
)
def test_get_playlist(generaldata, playlist):
    study = Mock()
    study.tree.get.return_value = generaldata
    assert FileStudyHelpers.get_playlist(study) == playlist


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
    ]
    FileStudyHelpers.set_playlist(study, [2, 4])
    FileStudyHelpers.set_playlist(study, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    FileStudyHelpers.set_playlist(study, [2, 3, 4, 7, 8, 9])
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
                    "general": {"nbyears": 10, "user-playlist": False},
                    "playlist": {
                        "playlist_reset": True,
                        "playlist_year -": [1, 2],
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
        ]
    )
