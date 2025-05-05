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

import pytest
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


@pytest.mark.unit_test
class TestArea:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_area(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=820)
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        client.post(f"/v1/studies/{study_id}/areas", json={"name": "area1", "type": "AREA"})
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "area2", "type": "AREA"})

        res = client.get(f"/v1/studies/{study_id}/areas?ui=true")
        assert res.status_code == 200
        expected = {
            "area1": {
                "layerColor": {"0": "230, 108, 44"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "ui": {"color_b": 44, "color_g": 108, "color_r": 230, "layers": "0", "x": 0, "y": 0},
            },
            "area2": {
                "layerColor": {"0": "230, 108, 44"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "ui": {"color_b": 44, "color_g": 108, "color_r": 230, "layers": "0", "x": 0, "y": 0},
            },
        }
        assert res.json() == expected

        client.put(
            f"/v1/studies/{study_id}/areas/area1/ui",
            json={
                "x": 10,
                "y": 10,
                "layerColor": {"0": "100, 100, 100"},
                "layerX": {"0": 10},
                "layerY": {"0": 10},
                "color_rgb": (100, 100, 100),
            },
        )

        res = client.get(f"/v1/studies/{study_id}/areas?ui=true")
        assert res.status_code == 200
        expected = {
            "area1": {
                "layerColor": {"0": "100, 100, 100"},
                "layerX": {"0": 10},
                "layerY": {"0": 10},
                "ui": {"color_b": 100, "color_g": 100, "color_r": 100, "layers": "0", "x": 10, "y": 10},
            },
            "area2": {
                "layerColor": {"0": "230, 108, 44"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "ui": {"color_b": 44, "color_g": 108, "color_r": 230, "layers": "0", "x": 0, "y": 0},
            },
        }
        assert res.json() == expected
