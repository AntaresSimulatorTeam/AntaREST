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
from starlette.testclient import TestClient


def test_list_outputs(admin_client: TestClient, internal_study_id: str):
    client = admin_client

    res = client.get(f"/v1/studies/{internal_study_id}/outputs")

    assert res.status_code == 200

    # All the data checked here are known to be used by some of our clients,
    # in particular the "settings" section.
    # If it's to be removed in the future, we need to coordinate with them.
    assert res.json() == [
        {
            "archived": False,
            "byYear": True,
            "mode": "Economy",
            "name": "20201014-1422eco-hello",
            "nbYears": 1,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "2030",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Economy",
                    "nbyears": 1,
                    "simulation.end": 7,
                    "simulation.start": 1,
                    "user-playlist": True,
                    "year-by-year": True,
                },
                "optimization": {"transmission-capacities": True},
                "playlist": [1],
            },
            "synthesis": True,
        },
        {
            "archived": False,
            "byYear": True,
            "mode": "Economy",
            "name": "20201014-1425eco-goodbye",
            "nbYears": 2,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "2030",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Economy",
                    "nbyears": 2,
                    "simulation.end": 14,
                    "simulation.start": 1,
                    "user-playlist": True,
                    "year-by-year": True,
                },
                "optimization": {"transmission-capacities": True},
                "playlist": [1, 2],
            },
            "synthesis": True,
        },
        {
            "archived": False,
            "byYear": False,
            "mode": "Economy",
            "name": "20201014-1427eco",
            "nbYears": 1,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "2030",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Economy",
                    "nbyears": 1,
                    "simulation.end": 7,
                    "simulation.start": 1,
                    "user-playlist": True,
                    "year-by-year": False,
                },
                "optimization": {"transmission-capacities": True},
                "playlist": [1],
            },
            "synthesis": True,
        },
        {
            "archived": False,
            "byYear": False,
            "mode": "Adequacy",
            "name": "20201014-1430adq",
            "nbYears": 1,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "2030",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Adequacy",
                    "nbyears": 1,
                    "simulation.end": 7,
                    "simulation.start": 1,
                    "user-playlist": True,
                    "year-by-year": False,
                },
                "optimization": {"transmission-capacities": True},
                "playlist": [1],
            },
            "synthesis": True,
        },
        {
            "archived": True,
            "byYear": False,
            "mode": "Adequacy",
            "name": "20201014-1430adq-2",
            "nbYears": 1,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "2030",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Adequacy",
                    "nbyears": 1,
                    "simulation.end": 7,
                    "simulation.start": 1,
                    "user-playlist": True,
                    "year-by-year": False,
                },
                "optimization": {"transmission-capacities": True},
                "playlist": [1],
            },
            "synthesis": True,
        },
        {
            "archived": False,
            "byYear": True,
            "mode": "Economy",
            "name": "20241807-1540eco-extra-outputs",
            "nbYears": 1,
            "settings": {
                "general": {
                    "first-month-in-year": "january",
                    "first.weekday": "Monday",
                    "horizon": "",
                    "january.1st": "Monday",
                    "leapyear": False,
                    "mode": "Economy",
                    "nbyears": 1,
                    "simulation.end": 365,
                    "simulation.start": 1,
                    "user-playlist": False,
                    "year-by-year": True,
                },
                "optimization": {"transmission-capacities": "local-values"},
                "playlist": [],
            },
            "synthesis": True,
        },
    ]
