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

from httpx import Headers
from starlette.testclient import TestClient


class TestConfigPlaylist:
    """
    Test the end points related to the playlist.
    """

    def test_nominal_case(self, client: TestClient, user_access_token: str) -> None:
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        base_study_res = client.post("/v1/studies?name=foo")
        study_id = base_study_res.json()

        res = client.get(f"/v1/studies/{study_id}/config/playlist/form")
        assert res.status_code == 200
        assert res.json() == {"1": {"status": True, "weight": 1}}

        res = client.post(f"/v1/studies/{study_id}/raw?path=settings/generaldata/general/nbyears", json=5)
        assert res.status_code == 200

        res = client.put(
            f"/v1/studies/{study_id}/config/playlist/form",
            json={"1": {"status": False, "weight": 8.4}, "2": {"status": False}, "4": {"weight": 2.1}},
        )
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{study_id}/config/playlist/form")
        assert res.status_code == 200
        assert res.json() == {
            "1": {"status": False, "weight": 8.4},
            "2": {"status": False, "weight": 1},
            "3": {"status": True, "weight": 1},
            "4": {"status": True, "weight": 2.1},
            "5": {"status": True, "weight": 1},
        }

        # Ensures we're able to modify the weight of an unactive year
        res = client.put(f"/v1/studies/{study_id}/config/playlist/form", json={"1": {"weight": 3}})
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{study_id}/config/playlist/form")
        assert res.status_code == 200
        assert res.json() == {
            "1": {"status": False, "weight": 3},
            "2": {"status": False, "weight": 1},
            "3": {"status": True, "weight": 1},
            "4": {"status": True, "weight": 2.1},
            "5": {"status": True, "weight": 1},
        }
