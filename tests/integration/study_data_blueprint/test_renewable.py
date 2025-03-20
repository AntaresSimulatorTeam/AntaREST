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

"""
## End-to-end test of the renewable cluster management.

We should consider the following scenario parameters :
* study type: `["raw", "variant"]`
  - user/bot can manage properties/matrices indifferently for raw or variant studies.
* token: `["user_token", "bot_token"]`  (bot = application token)
  - an authenticated user with the right permission (WRITE) can manage clusters,
  - we can use a bot token to manage clusters.
* study permission:
  - `StudyPermissionType.READ`: user/bot can only read properties/matrices,
  - `StudyPermissionType.RUN`: user/bot has no permission to manage clusters,
  - `StudyPermissionType.WRITE`: user/bot can manage cluster properties/matrices,
  - `StudyPermissionType.MANAGE_PERMISSIONS`: user/bot has no permission to manage clusters.

We should test the following end poins:
* create a cluster (with only a name/with all properties)
* read the properties of a cluster
* read the matrices of a cluster
* read the list of clusters
* update a cluster (all the properties/a single property)
* update the matrices of a cluster
* delete a cluster (or several clusters)
* validate the consistency of the matrices (and properties)
"""

import re
import time
import typing as t

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.string import to_camel_case
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableProperties
from tests.integration.utils import wait_task_completion

DEFAULT_PROPERTIES = RenewableProperties(name="Dummy").model_dump(mode="json")
DEFAULT_PROPERTIES = {to_camel_case(k): v for k, v in DEFAULT_PROPERTIES.items() if k != "name"}

# noinspection SpellCheckingInspection
EXISTING_CLUSTERS = []


@pytest.mark.unit_test
class TestRenewable:
    def test_lifecycle(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        # Upgrade study to version 810
        res = client.put(
            f"/v1/studies/{internal_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": 810},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # =====================
        #  General Data Update
        # =====================

        # Parameter 'renewable-generation-modelling' must be set to 'clusters' instead of 'aggregated'.
        # The `enr_modelling` value must be set to "clusters" instead of "aggregated"
        args = {
            "target": "settings/generaldata/other preferences",
            "data": {"renewable-generation-modelling": "clusters"},
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "update_config", "args": args}],
        )
        assert res.status_code == 200, res.json()

        # =============================
        #  RENEWABLE CLUSTER CREATION
        # =============================

        area_id = transform_name_to_id("FR")
        fr_solar_pv = "FR Solar PV"

        # Un attempt to create a renewable cluster without name
        # should raise a validation error (other properties are optional).
        # Un attempt to create a renewable cluster with an empty name
        # or an invalid name should also raise a validation error.
        attempts = [{}, {"name": ""}, {"name": "!??"}]
        for attempt in attempts:
            res = client.post(
                f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
                headers={"Authorization": f"Bearer {user_access_token}"},
                json=attempt,
            )
            assert res.status_code == 422, res.json()
            assert res.json()["exception"] in {"ValidationError", "RequestValidationError"}, res.json()

        # We can create a renewable cluster with the following properties:
        fr_solar_pv_props = {
            **DEFAULT_PROPERTIES,
            "name": fr_solar_pv,
            "group": "Solar PV",
            "nominalCapacity": 5001,
            "unitCount": 1,
            "tsInterpretation": "production-factor",
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=fr_solar_pv_props,
        )
        assert res.status_code == 200, res.json()
        fr_solar_pv_id = res.json()["id"]
        assert fr_solar_pv_id == transform_name_to_id(fr_solar_pv, lower=False)
        # noinspection SpellCheckingInspection
        expected_fr_solar_pv_cfg = {"id": fr_solar_pv_id, **fr_solar_pv_props}
        expected_fr_solar_pv_cfg["group"] = "solar pv"
        assert res.json() == expected_fr_solar_pv_cfg

        # reading the properties of a renewable cluster
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == expected_fr_solar_pv_cfg

        # =============================
        #  RENEWABLE CLUSTER MATRICES
        # =============================

        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/renewables/series/{area_id}/{fr_solar_pv_id.lower()}/series"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            json=[{"action": "replace_matrix", "args": args}],
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": matrix_path},
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # ==================================
        #  RENEWABLE CLUSTER LIST / GROUPS
        # ==================================

        # Reading the list of renewable clusters
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == EXISTING_CLUSTERS + [expected_fr_solar_pv_cfg]

        # updating properties
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "FR Solar pv old 1",
                "nominalCapacity": 5132,
            },
        )
        assert res.status_code == 200, res.json()
        expected_fr_solar_pv_cfg = {
            **expected_fr_solar_pv_cfg,
            "name": "FR Solar pv old 1",
            "nominalCapacity": 5132,
        }
        assert res.json() == expected_fr_solar_pv_cfg

        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == expected_fr_solar_pv_cfg

        # ===========================
        #  RENEWABLE CLUSTER UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "nominalCapacity": 2260,
                "tsInterpretation": "power-generation",
            },
        )
        expected_fr_solar_pv_cfg = {
            **expected_fr_solar_pv_cfg,
            "nominalCapacity": 2260,
            "tsInterpretation": "power-generation",
        }
        assert res.status_code == 200, res.json()
        assert res.json() == expected_fr_solar_pv_cfg

        # An attempt to update the `unitCount` property with an invalid value
        # should raise a validation error.
        # The `unitCount` property must be an integer greater than 0.
        bad_properties = {"unitCount": 0}
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=bad_properties,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "RequestValidationError", res.json()

        # The renewable cluster properties should not have been updated.
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == expected_fr_solar_pv_cfg

        # ===============================
        #  RENEWABLE CLUSTER DUPLICATION
        # ===============================

        new_name = "Duplicate of SolarPV"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/renewables/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"newName": new_name},
        )
        # asserts the config is the same
        assert res.status_code in {200, 201}, res.json()
        duplicated_config = dict(expected_fr_solar_pv_cfg)
        duplicated_config["name"] = new_name
        duplicated_id = transform_name_to_id(new_name, lower=False)
        duplicated_config["id"] = duplicated_id
        assert res.json() == duplicated_config

        # asserts the matrix has also been duplicated
        new_cluster_matrix_path = f"input/renewables/series/{area_id}/{duplicated_id.lower()}/series"
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": new_cluster_matrix_path},
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # =============================
        #  RENEWABLE CLUSTER DELETION
        # =============================

        # To delete a renewable cluster, we need to provide its ID.
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_solar_pv_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # If the renewable cluster list is empty, the deletion should be a no-op.
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # It's possible to delete multiple renewable clusters at once.
        # Create two clusters
        other_cluster_name = "Other Cluster 1"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": other_cluster_name},
        )
        assert res.status_code == 200, res.json()
        other_cluster_id1 = res.json()["id"]

        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": "Other Cluster 2"},
        )
        assert res.status_code == 200, res.json()
        other_cluster_id2 = res.json()["id"]

        # We can delete two renewable clusters at once.
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[other_cluster_id2, duplicated_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # There should only be one remaining cluster
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200
        obj = res.json()
        assert len(obj) == 1

        # ===========================
        #  RENEWABLE CLUSTER ERRORS
        # ===========================

        # Check DELETE with the wrong value of `area_id`
        bad_area_id = "bad_area"
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_solar_pv_id],
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(
            re.escape("Area 'bad_area' does not exist"),
            description,
            flags=re.IGNORECASE,
        )

        # Check DELETE with the wrong value of `study_id`
        bad_study_id = "bad_study"
        res = client.request(
            "DELETE",
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_solar_pv_id],
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check GET with wrong `area_id`
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check GET with wrong `study_id`
        res = client.get(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `study_id`
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": fr_solar_pv, "group": "Battery"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `area_id`
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": fr_solar_pv,
                "group": "Wind Onshore",
                "nominalCapacity": 617,
                "unitCount": 2,
                "tsInterpretation": "production-factor",
            },
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"Area ", description, flags=re.IGNORECASE)
        assert re.search(r"does not exist ", description, flags=re.IGNORECASE)

        # Check POST with wrong `group`
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": fr_solar_pv, "group": "GroupFoo"},
        )
        assert res.status_code == 200, res.json()
        obj = res.json()
        # If a group is not found, return the default group ("Other RES 1" by default).
        assert obj["group"] == "other res 1"

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "group": "Wind Onshore",
                "nominalCapacity": 617,
                "unitCount": 2,
                "tsInterpretation": "production-factor",
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"is not found", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `cluster_id`
        bad_cluster_id = "bad_cluster"
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable/{bad_cluster_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "group": "Wind Onshore",
                "nominalCapacity": 617,
                "unitCount": 2,
                "tsInterpretation": "production-factor",
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_cluster_id in description
        assert re.search(re.escape("'bad_cluster' not found"), description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `study_id`
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "group": "Wind Onshore",
                "nominalCapacity": 617,
                "unitCount": 2,
                "tsInterpretation": "production-factor",
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_study_id in description

        # Cannot duplicate a fake cluster
        unknown_id = "unknown"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/renewables/{unknown_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"newName": "duplicata"},
        )
        assert res.status_code == 404
        obj = res.json()
        assert f"'{unknown_id}' not found" in obj["description"]
        assert obj["exception"] == "RenewableClusterNotFound"

        # Cannot duplicate with an existing id
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/renewables/{other_cluster_id1}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"newName": other_cluster_name.upper()},  # different case, but same ID
        )
        assert res.status_code == 409, res.json()
        obj = res.json()
        description = obj["description"]
        assert other_cluster_name.upper() in description
        assert obj["exception"] == "DuplicateRenewableCluster"

    @pytest.fixture(name="base_study_id")
    def base_study_id_fixture(self, request: t.Any, client: TestClient, user_access_token: str) -> str:
        """Prepare a managed study for the variant study tests."""
        params = request.param
        res = client.post(
            "/v1/studies",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params=params,
        )
        assert res.status_code in {200, 201}, res.json()
        study_id: str = res.json()
        return study_id

    @pytest.fixture(name="variant_id")
    def variant_id_fixture(self, request: t.Any, client: TestClient, user_access_token: str, base_study_id: str) -> str:
        """Prepare a variant study for the variant study tests."""
        name = request.param
        res = client.post(
            f"/v1/studies/{base_study_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": name},
        )
        assert res.status_code in {200, 201}, res.json()
        study_id: str = res.json()
        return study_id

    # noinspection PyTestParametrized
    @pytest.mark.parametrize("base_study_id", [{"name": "Base Study", "version": 860}], indirect=True)
    @pytest.mark.parametrize("variant_id", ["Variant Study"], indirect=True)
    def test_variant_lifecycle(self, client: TestClient, user_access_token: str, variant_id: str) -> None:
        """
        In this test, we want to check that renewable clusters can be managed
        in the context of a "variant" study.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Create an area
        area_name = "France"
        res = client.post(f"/v1/studies/{variant_id}/areas", json={"name": area_name, "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()
        area_cfg = res.json()
        area_id = area_cfg["id"]

        # Create a renewable cluster
        cluster_name = "Th1"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/clusters/renewable",
            json={
                "name": cluster_name,
                "group": "Wind Offshore",
                "unitCount": 13,
                "nominalCapacity": 42500,
            },
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_id: str = res.json()["id"]

        # Update the renewable cluster
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/clusters/renewable/{cluster_id}", json={"unitCount": 15}
        )
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["unitCount"] == 15

        # Update the series matrix
        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/renewables/series/{area_id}/{cluster_id.lower()}/series"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(f"/v1/studies/{variant_id}/commands", json=[{"action": "replace_matrix", "args": args}])
        assert res.status_code in {200, 201}, res.json()

        # Duplicate the renewable cluster
        new_name = "Th2"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/renewables/{cluster_id}", params={"newName": new_name}
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["name"] == new_name
        new_id = cluster_cfg["id"]

        # Check that the duplicate has the right properties
        res = client.get(f"/v1/studies/{variant_id}/areas/{area_id}/clusters/renewable/{new_id}")
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["group"] == "wind offshore"
        assert cluster_cfg["unitCount"] == 15
        assert cluster_cfg["nominalCapacity"] == 42500

        # Check that the duplicate has the right matrix
        new_cluster_matrix_path = f"input/renewables/series/{area_id}/{new_id.lower()}/series"
        res = client.get(f"/v1/studies/{variant_id}/raw", params={"path": new_cluster_matrix_path})
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # Delete the renewable cluster
        # usage of request instead of delete as httpx doesn't support delete with a payload anymore.
        res = client.request(
            method="DELETE", url=f"/v1/studies/{variant_id}/areas/{area_id}/clusters/renewable", json=[cluster_id]
        )
        assert res.status_code == 204, res.json()

        # Check the list of variant commands
        res = client.get(f"/v1/studies/{variant_id}/commands")
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 7
        actions = [command["action"] for command in commands]
        assert actions == [
            "create_area",
            "create_renewables_cluster",
            "update_renewable_clusters",
            "replace_matrix",
            "create_renewables_cluster",
            "replace_matrix",
            "remove_renewables_cluster",
        ]

    def test_update_multiple_renewable_clusters(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a study with one area
        res = client.post("/v1/studies", params={"name": "study_test", "version": "8.8"})
        study_id = res.json()
        area_id = "area_1"
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": area_id, "type": "AREA"})
        res.raise_for_status()

        # Creates 50 renewable clusters inside the same area
        body = {}
        for k in range(50):
            cluster_id = f"th_{k}"
            res = client.post(f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable", json={"name": cluster_id})
            res.raise_for_status()
            body[f"{area_id} / {cluster_id}"] = {"enabled": False}

        # Modify all of them with the table-mode endpoint. Due to new code this should be pretty fast.
        start = time.time()
        res = client.put(f"/v1/studies/{study_id}/table-mode/renewables", json=body)
        end = time.time()
        assert res.status_code in {200, 201}
        duration = end - start
        assert duration < 1

        # Asserts the changes are effective.
        res = client.get(f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable")
        assert res.status_code == 200
        for renewable in res.json():
            assert renewable["enabled"] is False

        # Create a variant from the study
        res = client.post(f"/v1/studies/{study_id}/variants?name=var_1")
        study_id = res.json()

        # Update all renewables
        new_body = {}
        for key in body.keys():
            new_body[key] = {"nominalCapacity": 14}
        res = client.put(f"/v1/studies/{study_id}/table-mode/renewables", json=new_body)
        assert res.status_code in {200, 201}

        # Asserts changes are effective
        res = client.get(f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable")
        assert res.status_code == 200
        for thermal in res.json():
            assert thermal["enabled"] is False
            assert thermal["nominalCapacity"] == 14

        # Asserts only one command is created, and it's update_renewable_clusters
        res = client.get(f"/v1/studies/{study_id}/commands")
        assert res.status_code == 200
        json_result = res.json()
        assert len(json_result) == 1
        assert json_result[0]["action"] == "update_renewable_clusters"
