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

"""
Integration tests for Area operations in DATABASE storage mode.

These tests verify end-to-end functionality when studies use database storage
instead of filesystem storage for area data.

NOTE: Currently, the DATABASE storage mode is a POC that only implements basic
area operations via the DAO. The CREATE_AREA command also configures hydro management
and other elements that are not yet implemented in the database DAO.
Tests that require full command execution are marked as xfail until all required
DAO methods are implemented.
"""

import pytest
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy

# Reason for xfail - CREATE_AREA command requires methods not yet implemented in DatabaseStudyDao
DATABASE_MODE_INCOMPLETE = (
    "DATABASE storage mode POC: CREATE_AREA command requires save_hydro_management and other methods "
    "not yet implemented in DatabaseStudyDao"
)


class TestAreaDatabaseMode:
    """
    End-to-end tests for area operations in DATABASE storage mode.
    """

    def test_create_study_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that a study can be created in DATABASE storage mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("database-mode-study", version=870, storage_mode="database")

        # Verify study was created
        res = client.get(
            f"/v1/studies/{study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        study_data = res.json()
        assert study_data["id"] == study_id
        assert study_data["name"] == "database-mode-study"

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_create_and_list_areas_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test creating areas in a DATABASE mode study and listing them.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-areas-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create areas
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "Paris", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()

        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "London", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()

        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "Berlin", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()

        # List areas with UI info
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        areas = res.json()

        # Verify all areas exist with correct default UI
        assert len(areas) == 3
        assert "paris" in areas
        assert "london" in areas
        assert "berlin" in areas

        # Check default UI values
        for area_id in ["paris", "london", "berlin"]:
            area_ui = areas[area_id]
            assert area_ui["ui"]["x"] == 0
            assert area_ui["ui"]["y"] == 0
            assert area_ui["ui"]["color_r"] == 230
            assert area_ui["ui"]["color_g"] == 108
            assert area_ui["ui"]["color_b"] == 44
            assert area_ui["layerX"] == {"0": 0}
            assert area_ui["layerY"] == {"0": 0}
            assert area_ui["layerColor"] == {"0": "230, 108, 44"}

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_update_area_ui_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test updating area UI properties in DATABASE mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-ui-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create an area
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "TestArea", "type": "AREA"}, headers=headers)
        assert res.status_code == 200

        # Update UI
        res = client.put(
            f"/v1/studies/{study_id}/areas/testarea/ui",
            json={"x": 150, "y": 250, "colorRgb": [100, 150, 200]},
            headers=headers,
        )
        assert res.status_code == 200, res.json()

        # Verify UI was updated
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        areas = res.json()

        testarea_ui = areas["testarea"]
        assert testarea_ui["ui"]["x"] == 150
        assert testarea_ui["ui"]["y"] == 250
        assert testarea_ui["ui"]["color_r"] == 100
        assert testarea_ui["ui"]["color_g"] == 150
        assert testarea_ui["ui"]["color_b"] == 200
        assert testarea_ui["layerX"] == {"0": 150}
        assert testarea_ui["layerY"] == {"0": 250}
        assert testarea_ui["layerColor"] == {"0": "100, 150, 200"}

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_delete_area_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test deleting an area in DATABASE mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-delete-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create areas
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "ToDelete", "type": "AREA"}, headers=headers)
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "ToKeep", "type": "AREA"}, headers=headers)

        # Verify both areas exist
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 2

        # Delete one area
        res = client.delete(f"/v1/studies/{study_id}/areas/todelete", headers=headers)
        assert res.status_code == 200, res.json()

        # Verify only one area remains
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        areas = res.json()
        assert len(areas) == 1
        assert "tokeep" in areas
        assert "todelete" not in areas

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_area_duplicate_name_error_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that creating a duplicate area raises an error in DATABASE mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-duplicate-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create first area
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "UniqueArea", "type": "AREA"}, headers=headers)
        assert res.status_code == 200

        # Try to create area with same name (should fail)
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "UniqueArea", "type": "AREA"}, headers=headers)
        assert res.status_code != 200  # Should return an error

    def test_multiple_areas_with_layers_in_database_mode(self, client: TestClient, user_access_token: str) -> None:
        """
        Test creating multiple areas and updating their UI for different layers in DATABASE mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-layers-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create areas
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "Area1", "type": "AREA"}, headers=headers)
        client.post(f"/v1/studies/{study_id}/areas", json={"name": "Area2", "type": "AREA"}, headers=headers)

        # Update UI for layer 0
        client.put(
            f"/v1/studies/{study_id}/areas/area1/ui",
            json={"x": 100, "y": 100, "colorRgb": [255, 0, 0]},
            headers=headers,
        )
        client.put(
            f"/v1/studies/{study_id}/areas/area2/ui",
            json={"x": 200, "y": 200, "colorRgb": [0, 255, 0]},
            headers=headers,
        )

        # Get all areas UI info
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        areas = res.json()

        # Verify Area1 UI
        assert areas["area1"]["ui"]["x"] == 100
        assert areas["area1"]["ui"]["y"] == 100
        assert areas["area1"]["ui"]["color_r"] == 255
        assert areas["area1"]["ui"]["color_g"] == 0
        assert areas["area1"]["ui"]["color_b"] == 0

        # Verify Area2 UI
        assert areas["area2"]["ui"]["x"] == 200
        assert areas["area2"]["ui"]["y"] == 200
        assert areas["area2"]["ui"]["color_r"] == 0
        assert areas["area2"]["ui"]["color_g"] == 255
        assert areas["area2"]["ui"]["color_b"] == 0

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_persistence_after_multiple_operations_in_database_mode(
        self, client: TestClient, user_access_token: str
    ) -> None:
        """
        Test that data persists correctly after multiple CRUD operations in DATABASE mode.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("db-persistence-test", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create 5 areas
        for i in range(1, 6):
            client.post(f"/v1/studies/{study_id}/areas", json={"name": f"Area{i}", "type": "AREA"}, headers=headers)

        # Update some areas
        client.put(
            f"/v1/studies/{study_id}/areas/area1/ui",
            json={"x": 10, "y": 10, "colorRgb": [10, 10, 10]},
            headers=headers,
        )
        client.put(
            f"/v1/studies/{study_id}/areas/area3/ui",
            json={"x": 30, "y": 30, "colorRgb": [30, 30, 30]},
            headers=headers,
        )

        # Delete some areas
        client.delete(f"/v1/studies/{study_id}/areas/area2", headers=headers)
        client.delete(f"/v1/studies/{study_id}/areas/area4", headers=headers)

        # Verify final state
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
        assert res.status_code == 200
        areas = res.json()

        # Should have 3 areas remaining
        assert len(areas) == 3
        assert "area1" in areas
        assert "area3" in areas
        assert "area5" in areas
        assert "area2" not in areas
        assert "area4" not in areas

        # Verify updated areas retained their changes
        assert areas["area1"]["ui"]["x"] == 10
        assert areas["area1"]["ui"]["y"] == 10
        assert areas["area3"]["ui"]["x"] == 30
        assert areas["area3"]["ui"]["y"] == 30

        # Verify non-updated area kept defaults
        assert areas["area5"]["ui"]["x"] == 0
        assert areas["area5"]["ui"]["y"] == 0


class TestDatabaseModeVsFilesystemMode:
    """
    Comparative tests to ensure DATABASE mode behaves consistently with FILESYSTEM mode.
    """

    def test_area_operations_consistency_filesystem(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that area operations work correctly in FILESYSTEM mode (baseline).
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("consistency-filesystem", version=870, storage_mode="filesystem")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create areas
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "area1", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "area2", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()

        # Get areas
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
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

        # Update UI
        res = client.put(
            f"/v1/studies/{study_id}/areas/area1/ui",
            json={"x": 10, "y": 10, "colorRgb": [100, 100, 100]},
            headers=headers,
        )
        assert res.status_code == 200, res.json()

        # Verify update
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
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

    @pytest.mark.xfail(reason=DATABASE_MODE_INCOMPLETE, strict=True)
    def test_area_operations_consistency_database(self, client: TestClient, user_access_token: str) -> None:
        """
        Test that area operations produce consistent results in DATABASE mode.
        Should behave identically to FILESYSTEM mode once fully implemented.
        """
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("consistency-database", version=870, storage_mode="database")

        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create areas
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "area1", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "area2", "type": "AREA"}, headers=headers)
        assert res.status_code == 200, res.json()

        # Get areas
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
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

        # Update UI
        res = client.put(
            f"/v1/studies/{study_id}/areas/area1/ui",
            json={"x": 10, "y": 10, "colorRgb": [100, 100, 100]},
            headers=headers,
        )
        assert res.status_code == 200, res.json()

        # Verify update
        res = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=headers)
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
