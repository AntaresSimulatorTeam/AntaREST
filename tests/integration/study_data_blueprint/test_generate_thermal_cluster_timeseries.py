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

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from tests.integration.assets import ASSETS_DIR
from tests.integration.prepare_proxy import PreparerProxy
from tests.integration.utils import wait_task_completion

TIMESERIES_ASSETS_DIR = ASSETS_DIR.joinpath("timeseries_generation")


class TestGenerateThermalClusterTimeseries:
    @staticmethod
    def _generate_timeseries(client: TestClient, user_access_token: str, study_id: str) -> TaskDTO:
        res = client.put(f"/v1/studies/{study_id}/timeseries/generate")
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id)
        return task

    def test_lifecycle_nominal(self, client: TestClient, user_access_token: str) -> None:
        # Study preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        # Set nb timeseries thermal to 3.
        nb_years = 3
        res = client.put(f"/v1/studies/{study_id}/timeseries/config", json={"thermal": {"number": nb_years}})
        assert res.status_code in {200, 201}

        # Create 1 cluster in area1
        cluster_1 = "Cluster 1"
        nominal_capacity_cluster_1 = 1000.0
        preparer.create_thermal(
            study_id, area1_id, name=cluster_1, group="Lignite", nominalCapacity=nominal_capacity_cluster_1
        )

        # Create 2 clusters in area1
        cluster_2 = "Cluster 2"
        cluster_3 = "Cluster 3"
        nominal_capacity_cluster_2 = 40.0
        preparer.create_thermal(
            study_id, area2_id, name=cluster_2, group="Nuclear", nominalCapacity=nominal_capacity_cluster_2
        )
        preparer.create_thermal(study_id, area2_id, name=cluster_3, group="Gas", genTs="force no generation")

        # Update modulation for Cluster 2.
        matrix = np.zeros(shape=(8760, 4)).tolist()
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/prepro/{area2_id}/{cluster_2.lower()}/modulation"},
            json=matrix,
        )
        assert res.status_code == 200

        # Timeseries generation should succeed
        task = self._generate_timeseries(client, user_access_token, study_id)
        assert task.status == TaskStatus.COMPLETED

        # Check matrices
        # First one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area1_id}/{cluster_1.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data[1] == nb_years * [nominal_capacity_cluster_1]
        # Second one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area2_id}/{cluster_2.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data[1] == nb_years * [0]  # should be zeros as the modulation matrix is only zeros
        # Third one
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area2_id}/{cluster_3.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data == 8760 * [[0]]  # no generation c.f. gen-ts parameter -> empty file -> default simulator value

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_errors_and_limit_cases(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        # Study Preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        cluster_name = "Cluster 1"
        preparer.create_thermal(study_id, area1_id, name=cluster_name, group="Lignite")
        # Puts the nominal power as a float
        body = {"nominalCapacity": 4.4}
        res = client.patch(f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal/{cluster_name}", json=body)
        assert res.status_code in {200, 201}
        # Timeseries generation should succeed and produce results as int.
        task = self._generate_timeseries(client, user_access_token, study_id)
        assert task.status == TaskStatus.COMPLETED
        # Check matrix contains 4 instead of 4.4
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/series/{area1_id}/{cluster_name.lower()}/series"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data == 8760 * [[4]]

        # Puts 1 as PO rate and 1 as FO rate
        modulation_matrix = np.ones(shape=(365, 6)).tolist()
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/thermal/prepro/{area1_id}/{cluster_name.lower()}/data"},
            json=modulation_matrix,
        )
        assert res.status_code == 200
        # Timeseries generation should succeed
        task = self._generate_timeseries(client, user_access_token, study_id)
        assert task.status == TaskStatus.COMPLETED

        # Puts nominal capacity at 0
        body = {"nominalCapacity": 0}
        res = client.patch(f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal/{cluster_name}", json=body)
        assert res.status_code in {200, 201}
        # Timeseries generation fails because there's no nominal power
        task = self._generate_timeseries(client, user_access_token, study_id)
        assert task.status == TaskStatus.FAILED
        assert (
            f"Area {area1_id}, cluster {cluster_name.lower()}: Nominal power must be strictly positive, got 0.0"
            in task.result.message
        )

    def test_advanced_results(self, client: TestClient, user_access_token: str) -> None:
        # Study Preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area_id = preparer.create_area(study_id, name="test")["id"]
        res = client.put(f"/v1/studies/{study_id}/timeseries/config", json={"thermal": {"number": 10}})
        cluster_id = "cluster_test"
        assert res.status_code in {200, 201}

        # Create cluster with specific properties
        body = {
            "name": cluster_id,
            "group": "Nuclear",
            "unitCount": 10,
            "nominalCapacity": 500,
            "volatilityForced": 0.5,
            "volatilityPlanned": 0.5,
            "lawPlanned": "geometric",
        }
        res = client.post(f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal", json=body)
        assert res.status_code in {200, 201}

        mapping = {
            "reference_case": {
                "modulation_to_1": False,
                "fo_duration_to_1": False,
                "po_duration_to_1": False,
                "february": False,
            },
            "case_1": {
                "modulation_to_1": False,
                "fo_duration_to_1": False,
                "po_duration_to_1": True,
                "february": True,
            },
            "case_2": {
                "modulation_to_1": True,
                "fo_duration_to_1": True,
                "po_duration_to_1": False,
                "february": True,
            },
            "case_3": {
                "modulation_to_1": True,
                "fo_duration_to_1": True,
                "po_duration_to_1": True,
                "february": False,
            },
        }
        for test_case, variations in mapping.items():
            # Replace modulation matrix
            modulation_matrix = np.ones(shape=(8760, 4))
            if not variations["modulation_to_1"]:
                modulation_matrix[:24, 2] = 0.5
                modulation_matrix[24:52, 2] = 0.1
            res = client.post(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"/input/thermal/prepro/{area_id}/{cluster_id}/modulation"},
                json=modulation_matrix.tolist(),
            )
            assert res.status_code == 200

            # Replace gen_ts matrix
            input_gen_ts = np.loadtxt(TIMESERIES_ASSETS_DIR.joinpath("input_gen_ts.txt"), delimiter="\t")
            if variations["february"]:
                input_gen_ts[:59, 0] = 2
                input_gen_ts[:59, 1] = 3
            if variations["fo_duration_to_1"]:
                input_gen_ts[:, 0] = 1
            if variations["po_duration_to_1"]:
                input_gen_ts[:, 1] = 1
            res = client.post(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"/input/thermal/prepro/{area_id}/{cluster_id}/data"},
                json=input_gen_ts.tolist(),
            )
            assert res.status_code == 200

            # Get expected matrix
            expected_matrix = np.loadtxt(TIMESERIES_ASSETS_DIR.joinpath(f"{test_case}.txt"), delimiter="\t").tolist()

            # Generate timeseries
            task = self._generate_timeseries(client, user_access_token, study_id)
            assert task.status == TaskStatus.COMPLETED

            # Compare results
            generated_matrix = client.get(
                f"/v1/studies/{study_id}/raw", params={"path": f"input/thermal/series/{area_id}/{cluster_id}/series"}
            ).json()["data"]
            if generated_matrix != expected_matrix:
                raise AssertionError(f"Test case {test_case} failed")
