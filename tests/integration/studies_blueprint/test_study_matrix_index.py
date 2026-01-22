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

from httpx import Headers
from starlette.testclient import TestClient


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
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

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
        client.headers = Headers({"Authorization": f"Bearer {user_access_token}"})

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
