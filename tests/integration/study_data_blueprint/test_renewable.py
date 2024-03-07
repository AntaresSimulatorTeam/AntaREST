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
import copy
import json
import re

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.string import to_camel_case
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableProperties
from tests.integration.utils import wait_task_completion

DEFAULT_PROPERTIES = json.loads(RenewableProperties(name="Dummy").json())
DEFAULT_PROPERTIES = {to_camel_case(k): v for k, v in DEFAULT_PROPERTIES.items() if k != "name"}

# noinspection SpellCheckingInspection
EXISTING_CLUSTERS = []


@pytest.mark.unit_test
class TestRenewable:
    def test_lifecycle(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        # Upgrade study to version 810
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
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
            f"/v1/studies/{study_id}/commands",
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
                f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=fr_solar_pv_props,
        )
        assert res.status_code == 200, res.json()
        fr_solar_pv_id = res.json()["id"]
        assert fr_solar_pv_id == transform_name_to_id(fr_solar_pv, lower=False)
        # noinspection SpellCheckingInspection
        fr_solar_pv_cfg = {"id": fr_solar_pv_id, **fr_solar_pv_props}
        assert res.json() == fr_solar_pv_cfg

        # reading the properties of a renewable cluster
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_solar_pv_cfg

        # =============================
        #  RENEWABLE CLUSTER MATRICES
        # =============================

        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/renewables/series/{area_id}/{fr_solar_pv_id.lower()}/series"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            json=[{"action": "replace_matrix", "args": args}],
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/raw",
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == EXISTING_CLUSTERS + [fr_solar_pv_cfg]

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "FR Solar pv old 1",
                "nominalCapacity": 5132,
            },
        )
        assert res.status_code == 200, res.json()
        fr_solar_pv_cfg = {
            **fr_solar_pv_cfg,
            "name": "FR Solar pv old 1",
            "nominalCapacity": 5132,
        }
        assert res.json() == fr_solar_pv_cfg

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_solar_pv_cfg

        # ===========================
        #  RENEWABLE CLUSTER UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "nominalCapacity": 2260,
                "tsInterpretation": "power-generation",
            },
        )
        fr_solar_pv_cfg = {
            **fr_solar_pv_cfg,
            "nominalCapacity": 2260,
            "tsInterpretation": "power-generation",
        }
        assert res.status_code == 200, res.json()
        assert res.json() == fr_solar_pv_cfg

        # An attempt to update the `unitCount` property with an invalid value
        # should raise a validation error.
        # The `unitCount` property must be an integer greater than 0.
        bad_properties = {"unitCount": 0}
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=bad_properties,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "RequestValidationError", res.json()

        # The renewable cluster properties should not have been updated.
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{fr_solar_pv_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_solar_pv_cfg

        # ===============================
        #  RENEWABLE CLUSTER DUPLICATION
        # ===============================

        new_name = "Duplicate of SolarPV"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/renewables/{fr_solar_pv_id}?new_cluster_name={new_name}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        # asserts the config is the same
        assert res.status_code in {200, 201}
        duplicated_config = copy.deepcopy(fr_solar_pv_cfg)
        duplicated_config["name"] = new_name
        duplicated_id = transform_name_to_id(new_name, lower=False)
        duplicated_config["id"] = duplicated_id
        assert res.json() == duplicated_config

        # asserts the matrix has also been duplicated
        new_cluster_matrix_path = f"input/renewables/series/{area_id}/{duplicated_id.lower()}/series"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_solar_pv_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # If the renewable cluster list is empty, the deletion should be a no-op.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # It's possible to delete multiple renewable clusters at once.
        # Create two clusters
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": "Other Cluster 1"},
        )
        assert res.status_code == 200, res.json()
        other_cluster_id1 = res.json()["id"]

        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": "Other Cluster 2"},
        )
        assert res.status_code == 200, res.json()
        other_cluster_id2 = res.json()["id"]

        # We can delete two renewable clusters at once.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[other_cluster_id2, duplicated_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # There should only be one remaining cluster
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
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
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/renewable",
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
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/renewable/{fr_solar_pv_id}",
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
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/renewable",
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": fr_solar_pv, "group": "GroupFoo"},
        )
        assert res.status_code == 200, res.json()
        obj = res.json()
        # If a group is not found, return the default group ("Other RES 1" by default).
        assert obj["group"] == "Other RES 1"

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/renewable/{fr_solar_pv_id}",
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
        assert re.search(r"not a child of ", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `cluster_id`
        bad_cluster_id = "bad_cluster"
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable/{bad_cluster_id}",
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
        fake_id = "fake_id"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/renewables/{fake_id}?new_cluster_name=duplicata",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 404
        obj = res.json()
        assert obj["description"] == f"Cluster: '{fake_id}' not found"
        assert obj["exception"] == "ClusterNotFound"

        # Cannot duplicate with an existing id
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/renewables/{other_cluster_id1}?new_cluster_name={other_cluster_id1}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 409
        obj = res.json()
        description = obj["description"]
        assert f"'{other_cluster_id1}'" in description
        assert obj["exception"] == "ClusterAlreadyExists"
