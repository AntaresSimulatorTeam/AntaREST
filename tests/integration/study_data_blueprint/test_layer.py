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

import pytest
from httpx import Headers
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


class TestLayer:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_layer_endpoints(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        """Test layer CRUD operations via HTTP endpoints"""
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        # Create some areas for layer assignment tests
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "area1", "type": "AREA"})
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "area2", "type": "AREA"})

        # Test GET layers - should have default layer "0" (All)
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        assert len(layers) == 1
        assert layers[0]["id"] == "0"
        assert layers[0]["name"] == "All"
        # Layer "0" (All) contains all areas by default
        assert sorted(layers[0]["areas"]) == ["area1", "area2"]

        # Test POST - Create a new layer
        res = client.post(f"/v1/studies/{study_id}/layers?name=Layer%20One")
        assert res.status_code == 200
        layer_id_1 = res.json()
        assert layer_id_1 == "1"

        # Test GET layers - should now have 2 layers
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        assert len(layers) == 2
        assert layers[1]["id"] == "1"
        assert layers[1]["name"] == "Layer One"
        assert layers[1]["areas"] == []

        # Test POST - Create another layer
        res = client.post(f"/v1/studies/{study_id}/layers?name=Layer%20Two")
        assert res.status_code == 200
        layer_id_2 = res.json()
        assert layer_id_2 == "2"

        res = client.put(f"/v1/studies/{study_id}/layers/{layer_id_1}?name=Updated%20Layer%20One")
        assert res.status_code == 200

        # Verify the layer name was updated
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        layer_1 = next(layer for layer in layers if layer["id"] == layer_id_1)
        assert layer_1["name"] == "Updated Layer One"

        # Test PUT - Update layer areas
        res = client.put(
            f"/v1/studies/{study_id}/layers/{layer_id_1}?name=Updated%20Layer%20One", json=["area1", "area2"]
        )
        assert res.status_code == 200

        # Verify the layer areas were updated
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        layer_1 = next(layer for layer in layers if layer["id"] == layer_id_1)
        assert sorted(layer_1["areas"]) == ["area1", "area2"]

        # Test PUT - Update only areas (name empty)
        res = client.put(f"/v1/studies/{study_id}/layers/{layer_id_2}", json=["area1"])
        assert res.status_code == 200

        # Verify only areas were updated, name should still be "Layer Two"
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        layer_2 = next(layer for layer in layers if layer["id"] == layer_id_2)
        assert layer_2["name"] == "Layer Two"
        assert layer_2["areas"] == ["area1"]

        res = client.put(f"/v1/studies/{study_id}/layers/1?name=FinalName")
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        layer_1 = next(layer for layer in layers if layer["id"] == "1")
        # The name should be "FinalName", NOT "1" (which was the bug)
        assert layer_1["name"] == "FinalName"
        assert layer_1["id"] == "1"

        # Test DELETE - Remove a layer
        res = client.delete(f"/v1/studies/{study_id}/layers/{layer_id_2}")
        assert res.status_code == 204

        # Verify the layer was deleted
        res = client.get(f"/v1/studies/{study_id}/layers")
        assert res.status_code == 200
        layers = res.json()
        assert len(layers) == 2  # Should have layer "0" and layer "1" only
        layer_ids = [layer["id"] for layer in layers]
        assert "2" not in layer_ids
