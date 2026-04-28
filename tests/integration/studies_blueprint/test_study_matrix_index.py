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
from starlette.testclient import TestClient

from antarest.study.model import StorageMode


class TestStudyMatrixIndex:
    """
    The goal of this test is to check that the API allows to retrieve
    information about the data matrices of a study.

    The values are used byt the frontend to display the time series
    with the right time column.
    """

    def test_get_study_matrix_index(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Check the matrix index for Thermal clusters
        # ===========================================

        # Check the Common matrix index
        res = client.get(
            f"/v1/studies/{internal_study_id}/matrixindex",
            params={"path": "input/thermal/prepro/fr/01_solar/modulation"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        # We expect to have an "hourly" time series with 8760 hours
        expected = {
            "first_week_size": 7,
            "level": "hourly",
            "start_date": "2018-01-01 00:00:00",
            "steps": 8760,
        }
        assert actual == expected

        # Check the TS Generator matrix index
        res = client.get(
            f"/v1/studies/{internal_study_id}/matrixindex", params={"path": "input/thermal/prepro/fr/01_solar/data"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        # We expect to have a "daily" time series with 365 days
        expected = {
            "first_week_size": 7,
            "level": "daily",
            "start_date": "2018-01-01 00:00:00",
            "steps": 365,
        }
        assert actual == expected

        # Check the time series
        res = client.get(
            f"/v1/studies/{internal_study_id}/matrixindex", params={"path": "input/thermal/series/fr/01_solar/series"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        # We expect to have an "hourly" time series with 8760 hours
        expected = {
            "first_week_size": 7,
            "level": "hourly",
            "start_date": "2018-01-01 00:00:00",
            "steps": 8760,
        }
        assert actual == expected

        # Check the default matrix index
        # ==============================

        res = client.get(f"/v1/studies/{internal_study_id}/matrixindex")
        assert res.status_code == 200
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "start_date": "2018-01-01 00:00:00",
            "steps": 8760,
            "level": "hourly",
        }
        assert actual == expected

        # Check the matrix index of a daily time series stored in the output folder
        # =========================================================================

        res = client.get(
            f"/v1/studies/{internal_study_id}/matrixindex",
            params={"path": "output/20201014-1427eco/economy/mc-all/areas/es/details-daily"},
        )
        assert res.status_code == 200
        actual = res.json()
        expected = {"first_week_size": 7, "start_date": "2018-01-01 00:00:00", "steps": 7, "level": "daily"}
        assert actual == expected

        # Check the matrix index for a weekly binding constraint
        # =========================================================================

        res = client.post(
            f"/v1/studies/{internal_study_id}/bindingconstraints", json={"name": "bc_1", "timeStep": "weekly"}
        )
        res.raise_for_status()
        res = client.get(
            f"/v1/studies/{internal_study_id}/matrixindex", params={"path": "input/bindingconstraints/bc_1"}
        )
        assert res.status_code == 200
        actual = res.json()
        expected = {"first_week_size": 7, "start_date": "2018-01-01 00:00:00", "steps": 365, "level": "daily"}
        assert actual == expected

    def test_get_output_time_index(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        Test the new time-index endpoint for outputs with different frequencies.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        output_id = "20201014-1427eco"

        # Test with default frequency (hourly)
        # =====================================
        res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/time-index")
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "level": "hourly",
            "start_date": "2018-01-01 00:00:00",
            "steps": 168,  # 7 days * 24 hours
        }
        assert actual == expected

        # Test with daily frequency
        # =========================
        res = client.get(
            f"/v1/studies/{internal_study_id}/output/{output_id}/time-index", params={"frequency": "daily"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "level": "daily",
            "start_date": "2018-01-01 00:00:00",
            "steps": 7,
        }
        assert actual == expected

        # Test with weekly frequency
        # ==========================
        res = client.get(
            f"/v1/studies/{internal_study_id}/output/{output_id}/time-index", params={"frequency": "weekly"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "level": "weekly",
            "start_date": "2018-01-01 00:00:00",
            "steps": 1,  # 7 days = 1 week
        }
        assert actual == expected

        # Test with monthly frequency
        # ===========================
        res = client.get(
            f"/v1/studies/{internal_study_id}/output/{output_id}/time-index", params={"frequency": "monthly"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "level": "monthly",
            "start_date": "2018-01-01 00:00:00",
            "steps": 1,  # 7 days span only 1 month (January)
        }
        assert actual == expected

        # Test with annual frequency
        # ==========================
        res = client.get(
            f"/v1/studies/{internal_study_id}/output/{output_id}/time-index", params={"frequency": "annual"}
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            "first_week_size": 7,
            "level": "annual",
            "start_date": "2018-01-01 00:00:00",
            "steps": 1,
        }
        assert actual == expected

    @pytest.mark.parametrize("mode", [StorageMode.DATABASE, StorageMode.FILESYSTEM])
    def test_for_both_type_of_studies(self, client: TestClient, user_access_token: str, mode: StorageMode) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a database study
        res = client.post(f"/v1/studies?name=study&storage_mode={mode}")
        assert res.status_code == 201, res.json()
        study_id = res.json()

        # Create areas, links, clusters, binding constraints and short-term storages to have various matrices
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "france"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "belgium"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": "france", "area2": "belgium"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/bindingconstraints", json={"name": "bc1"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/areas/france/clusters/thermal", json={"name": "th1"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/areas/france/clusters/renewable", json={"name": "r1"})
        res.raise_for_status()
        res = client.post(f"/v1/studies/{study_id}/areas/france/storages", json={"name": "st-storage"})
        res.raise_for_status()

        # Try to fetch the matrix index for different matrices
        url = f"/v1/studies/{study_id}/matrixindex"
        hourly_response = {"first_week_size": 7, "start_date": "2018-01-01 00:00:00", "steps": 8760, "level": "hourly"}
        daily_response = {"first_week_size": 7, "start_date": "2018-01-01 00:00:00", "steps": 365, "level": "daily"}

        # Hourly matrices
        for path in [
            "input/load/series/load_france",
            "input/wind/series/wind_france",
            "input/solar/series/solar_france",
            "input/misc-gen/miscgen-france",
            "input/reserves/france",
            "input/links/belgium/capacities/france_direct",
            "input/links/belgium/capacities/france_indirect",
            "input/thermal/prepro/france/th1/modulation",
            "input/thermal/series/france/th1/series",
            "input/thermal/series/france/th1/fuelCost",
            "input/thermal/series/france/th1/CO2Cost",
            "input/renewables/series/france/r1/series",
            "input/st-storage/series/france/st-storage/pmax_injection",
            "input/st-storage/series/france/st-storage/pmax_withdrawal",
            "input/st-storage/series/france/st-storage/lower_rule_curve",
            "input/st-storage/series/france/st-storage/upper_rule_curve",
            "input/st-storage/series/france/st-storage/inflows",
            "input/st-storage/series/france/st-storage/cost_injection",
            "input/st-storage/series/france/st-storage/cost_withdrawal",
            "input/st-storage/series/france/st-storage/cost_level",
            "input/st-storage/series/france/st-storage/cost_variation_injection",
            "input/st-storage/series/france/st-storage/cost_variation_withdrawal",
            "input/hydro/prepro/france/energy",
            "input/hydro/series/france/ror",
            "input/hydro/series/france/mingen",
            "input/hydro/common/capacity/creditmodulations_france",
        ]:
            res = client.get(url, params={"path": path})
            assert res.json() == hourly_response

        # Daily matrices
        for path in [
            "input/thermal/prepro/france/th1/data",
            "input/hydro/common/capacity/inflowPattern_france",
            "input/hydro/common/capacity/waterValues_france",
            "input/hydro/series/france/mod",
            "input/hydro/common/capacity/maxpower_france",
            "input/hydro/common/capacity/reservoir_france",
        ]:
            res = client.get(url, params={"path": path})
            assert res.json() == daily_response

        ############ Binding constraints ############
        bc_matrix_path = "input/bindingconstraints/bc1_eq"

        # At first the constraint is created with time_step HOURLY
        res = client.get(url, params={"path": bc_matrix_path})
        assert res.json() == hourly_response

        # We update the constraint to have a weekly time step
        res = client.put(f"/v1/studies/{study_id}/bindingconstraints/bc1", json={"timeStep": "weekly"})
        assert res.status_code == 200, res.json()

        # Now we should see the daily index for the constraint (weekly constraint means daily timestep)
        res = client.get(url, params={"path": bc_matrix_path})
        assert res.json() == daily_response

        # We update the constraint to have a daily time step
        res = client.put(f"/v1/studies/{study_id}/bindingconstraints/bc1", json={"timeStep": "daily"})
        assert res.status_code == 200, res.json()

        # We should still see the daily index for the constraint
        res = client.get(url, params={"path": bc_matrix_path})
        assert res.json() == daily_response
