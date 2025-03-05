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

import http
import typing as t

import pytest
from starlette.testclient import TestClient

from antarest.study.business.area_management import AreaInfoDTO, AreaType


@pytest.mark.unit_test
class TestHydroAllocation:
    """
    Test the end points related to hydraulic allocation.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_allocation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """Check `get_allocation_form_values` end point"""
        area_id = "de"
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/allocation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"allocation": [{"areaId": "de", "coefficient": 1.0}]}
        assert actual == expected

    def test_get_allocation_form_values__variant(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        The purpose of this test is to check that we can get the form parameters from a study variant.
        To prepare this test, we start from a RAW study, copy it to the managed study workspace
        and then create a variant from this managed workspace.
        """
        # Create a managed study from the RAW study.
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"dest": "Clone", "with_outputs": False, "use_task": False},
        )
        assert res.status_code == http.HTTPStatus.CREATED, res.json()
        managed_id = res.json()
        assert managed_id is not None

        # Ensure the managed study has the same allocation form as the RAW study.
        area_id = "de"
        res = client.get(
            f"/v1/studies/{managed_id}/areas/{area_id}/hydro/allocation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"allocation": [{"areaId": "de", "coefficient": 1.0}]}
        assert actual == expected

        # create a variant study from the managed study
        res = client.post(
            f"/v1/studies/{managed_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": "foo"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()  # should be CREATED
        variant_id = res.json()
        assert variant_id is not None

        # get allocation form
        area_id = "de"
        res = client.get(
            f"/v1/studies/{variant_id}/areas/{area_id}/hydro/allocation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {"allocation": [{"areaId": "de", "coefficient": 1.0}]}
        assert actual == expected

    @pytest.mark.parametrize(
        "area_id, expected",
        [
            pytest.param(
                "*",
                {
                    "columns": ["de", "es", "fr", "it"],
                    "data": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ],
                    "index": ["de", "es", "fr", "it"],
                },
                id="all-areas",
            ),
        ],
    )
    def test_get_allocation_matrix(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
        area_id: str,
        expected: t.List[t.List[float]],
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        """Check `get_allocation_matrix` end point"""
        res = client.get(f"/v1/studies/{internal_study_id}/areas/hydro/allocation/matrix")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual == expected

        # test get allocation matrix with a study with only one area.
        client.delete(f"/v1/studies/{internal_study_id}/areas/de")
        client.delete(f"/v1/studies/{internal_study_id}/areas/es")
        client.delete(f"/v1/studies/{internal_study_id}/areas/fr")
        res = client.get(f"/v1/studies/{internal_study_id}/areas/hydro/allocation/matrix")
        assert res.status_code == http.HTTPStatus.OK, res.json()
        assert res.json() == {"index": ["it"], "columns": ["it"], "data": [[1.0]]}

    def test_set_allocation_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """Check `set_allocation_form_values` end point"""
        area_id = "de"
        expected = {
            "allocation": [
                {"areaId": "de", "coefficient": 3},
                {"areaId": "es", "coefficient": 1.0},
            ]
        }
        res = client.put(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/allocation/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=expected,
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual == expected

        # check that the values are updated
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"path": "input/hydro/allocation", "depth": 3},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "de": {"[allocation]": {"de": 3.0, "es": 1.0}},
            "es": {"[allocation]": {"es": 1}},
            "fr": {"[allocation]": {"fr": 1}},
            "it": {"[allocation]": {"it": 1}},
        }
        assert actual == expected

    def test_create_area(self, client: TestClient, user_access_token: str, internal_study_id: str) -> None:
        """
        Given a study, when an area is created, the hydraulic allocation
        column for this area must be updated with the following values:
        - the coefficient == 1 for this area,
        - the coefficient == 0 for the other areas.
        Other columns must not be changed.
        """
        area_info = AreaInfoDTO(id="north", name="NORTH", type=AreaType.AREA)
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
            data=area_info.model_dump_json(),
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()

        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/hydro/allocation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK
        actual = res.json()
        expected = {
            "columns": ["de", "es", "fr", "it", "north"],
            "data": [
                [1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            "index": ["de", "es", "fr", "it", "north"],
        }
        assert actual == expected

    def test_delete_area(self, client: TestClient, user_access_token: str, internal_study_id: str) -> None:
        """
        Given a study, when an area is deleted, the hydraulic allocation
        column for this area must be removed.
        Other columns must be updated to reflect the area deletion.
        """
        # First change the coefficients to avoid zero values (which are defaults).
        obj = {
            "de": {"[allocation]": {"de": 10, "es": 20, "fr": 30, "it": 40}},
            "es": {"[allocation]": {"de": 11, "es": 21, "fr": 31, "it": 41}},
            "fr": {"[allocation]": {"de": 12, "es": 22, "fr": 32, "it": 42}},
            "it": {"[allocation]": {"de": 13, "es": 23, "fr": 33, "it": 43}},
        }
        for prod_area, allocation_cfg in obj.items():
            res = client.post(
                f"/v1/studies/{internal_study_id}/raw",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"path": f"input/hydro/allocation/{prod_area}"},
                json=allocation_cfg,
            )
            assert res.status_code == http.HTTPStatus.OK, res.json()

        # Then we remove the "fr" zone.
        # The deletion should update the allocation matrix of all other zones.
        res = client.delete(
            f"/v1/studies/{internal_study_id}/areas/fr",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()

        # Check that the "fr" column is removed from the hydraulic allocation matrix.
        # The row corresponding to "fr" must also be deleted.
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/hydro/allocation/matrix",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "columns": ["de", "es", "it"],
            "data": [
                [10.0, 11.0, 13.0],
                [20.0, 21.0, 23.0],
                [40.0, 41.0, 43.0],
            ],
            "index": ["de", "es", "it"],
        }
        assert actual == expected
