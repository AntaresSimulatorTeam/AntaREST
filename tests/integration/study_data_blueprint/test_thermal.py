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
## End-to-end test of the thermal cluster management.

We should consider the following scenario parameters :
* study version: `[860, 800]`:
  - `860`: user/bot can read/update all properties **including** new pollutant values.
  - `800`: user/bot can read/update all properties **excluding** new pollutant values:
    - an attempt to create or update a study with new pollutant values must raise an error.
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

import io
import re
import typing as t

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.core.utils.string import to_camel_case
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import ThermalProperties
from tests.integration.utils import wait_task_completion

DEFAULT_PROPERTIES = ThermalProperties(name="Dummy").model_dump(mode="json")
DEFAULT_PROPERTIES = {to_camel_case(k): v for k, v in DEFAULT_PROPERTIES.items() if k != "name"}

# noinspection SpellCheckingInspection
EXISTING_CLUSTERS = [
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "01_solar",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 10.0,
        "marketBidCost": 10.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "01_solar",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "02_wind_on",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 20.0,
        "marketBidCost": 20.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "02_wind_on",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "03_wind_off",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 30.0,
        "marketBidCost": 30.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "03_wind_off",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "04_res",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 40.0,
        "marketBidCost": 40.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "04_res",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "05_nuclear",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 50.0,
        "marketBidCost": 50.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "05_nuclear",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "06_coal",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 60.0,
        "marketBidCost": 60.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "06_coal",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "07_gas",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 70.0,
        "marketBidCost": 70.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "07_gas",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "08_non-res",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 80.0,
        "marketBidCost": 80.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "08_non-res",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global",
        "group": "other 1",
        "id": "09_hydro_pump",
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 90.0,
        "marketBidCost": 90.0,
        "minDownTime": 1,
        "minStablePower": 0.0,
        "minUpTime": 1,
        "mustRun": False,
        "name": "09_hydro_pump",
        "nominalCapacity": 1000000.0,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
]


def _upload_matrix(
    client: TestClient, user_access_token: str, study_id: str, matrix_path: str, df: pd.DataFrame
) -> None:
    tsv = io.BytesIO()
    df.to_csv(tsv, sep="\t", index=False, header=False)
    tsv.seek(0)
    res = client.put(
        f"/v1/studies/{study_id}/raw",
        params={"path": matrix_path},
        headers={"Authorization": f"Bearer {user_access_token}"},
        files={"file": tsv},
    )
    res.raise_for_status()


@pytest.mark.unit_test
class TestThermal:
    @pytest.mark.parametrize(
        "version", [pytest.param(0, id="No Upgrade"), pytest.param(860, id="v8.6"), pytest.param(870, id="v8.7")]
    )
    def test_lifecycle(self, client: TestClient, user_access_token: str, internal_study_id: str, version: int) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # =============================
        #  STUDY UPGRADE
        # =============================

        if version != 0:
            res = client.put(f"/v1/studies/{internal_study_id}/upgrade", params={"target_version": version})
            res.raise_for_status()
            task_id = res.json()
            task = wait_task_completion(client, user_access_token, task_id)
            from antarest.core.tasks.model import TaskStatus

            assert task.status == TaskStatus.COMPLETED, task

        # =================================
        #  UPDATE EXPECTED POLLUTANTS LIST
        # =================================

        # noinspection SpellCheckingInspection
        pollutants_names = ["nh3", "nmvoc", "nox", "op1", "op2", "op3", "op4", "op5", "pm10", "pm25", "pm5", "so2"]
        pollutants_values = 0.0 if version >= 860 else None
        for existing_cluster in EXISTING_CLUSTERS:
            existing_cluster.update({p: pollutants_values for p in pollutants_names})
            existing_cluster.update(
                {
                    "costGeneration": "SetManually" if version == 870 else None,
                    "efficiency": 100.0 if version == 870 else None,
                    "variableOMCost": 0.0 if version == 870 else None,
                }
            )

        # ==========================
        #  THERMAL CLUSTER CREATION
        # ==========================

        area_id = transform_name_to_id("FR")
        fr_gas_conventional = "FR_Gas conventional"

        # Un attempt to create a thermal cluster without name
        # should raise a validation error (other properties are optional).
        # Un attempt to create a thermal cluster with an empty name
        # or an invalid name should also raise a validation error.
        attempts = [{}, {"name": ""}, {"name": "!??"}]
        for attempt in attempts:
            res = client.post(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=attempt)
            assert res.status_code == 422, res.json()
            assert res.json()["exception"] in {"ValidationError", "RequestValidationError"}, res.json()

        # creating a thermal cluster with a name as a string should not raise an Exception
        res = client.post(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json={"name": 111})
        assert res.status_code == 200, res.json()
        res = client.request(
            "DELETE", f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=["111"]
        )
        assert res.status_code == 204, res.json()

        # We can create a thermal cluster with the following properties:
        fr_gas_conventional_props = {
            **DEFAULT_PROPERTIES,
            "name": fr_gas_conventional,
            "group": "gas",
            "unitCount": 15,
            "nominalCapacity": 31.6,
            "minStablePower": 5.4984,
            "minUpTime": 5,
            "minDownTime": 5,
            "co2": 0.57,
            "marginalCost": 181.267,
            "startupCost": 6035.6,
            "marketBidCost": 181.267,
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=fr_gas_conventional_props
        )
        assert res.status_code == 200, res.json()
        fr_gas_conventional_id = res.json()["id"]
        assert fr_gas_conventional_id == transform_name_to_id(fr_gas_conventional, lower=False)
        # noinspection SpellCheckingInspection
        fr_gas_conventional_cfg = {
            **fr_gas_conventional_props,
            "id": fr_gas_conventional_id,
            **{p: pollutants_values for p in pollutants_names},
        }
        fr_gas_conventional_cfg = {
            **fr_gas_conventional_cfg,
            **{
                "costGeneration": "SetManually" if version == 870 else None,
                "efficiency": 100.0 if version == 870 else None,
                "variableOMCost": 0.0 if version == 870 else None,
            },
        }
        assert res.json() == fr_gas_conventional_cfg

        # reading the properties of a thermal cluster
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # asserts it didn't break the allocation matrix
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/hydro/allocation/form")
        assert res.status_code == 200, res.json()

        # ==========================
        #  THERMAL CLUSTER MATRICES
        # ==========================

        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/thermal/prepro/{area_id}/{fr_gas_conventional_id.lower()}/data"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands", json=[{"action": "replace_matrix", "args": args}]
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": matrix_path})
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # ==================================
        #  THERMAL CLUSTER LIST / GROUPS
        # ==================================

        # Reading the list of thermal clusters
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal")
        assert res.status_code == 200, res.json()
        assert res.json() == EXISTING_CLUSTERS + [fr_gas_conventional_cfg]

        # updating properties
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={
                "name": "FR_Gas conventional old 1",
                "nominalCapacity": 32.1,
            },
        )
        assert res.status_code == 200, res.json()
        fr_gas_conventional_cfg = {
            **fr_gas_conventional_cfg,
            "name": "FR_Gas conventional old 1",
            "nominalCapacity": 32.1,
        }
        assert res.json() == fr_gas_conventional_cfg

        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # ===========================
        #  THERMAL CLUSTER UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={
                "marginalCost": 182.456,
                "startupCost": 6140.8,
                "marketBidCost": 182.456,
            },
        )
        fr_gas_conventional_cfg = {
            **fr_gas_conventional_cfg,
            "marginalCost": 182.456,
            "startupCost": 6140.8,
            "marketBidCost": 182.456,
        }
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # An attempt to update the `unitCount` property with an invalid value
        # should raise a validation error.
        # The `unitCount` property must be an integer greater than 0.
        bad_properties = {"unitCount": 0}
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json=bad_properties,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "RequestValidationError", res.json()

        # The thermal cluster properties should not have been updated.
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # Update with a pollutant. Should succeed even with versions prior to v8.6
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={"nox": 10.0},
        )
        assert res.status_code == 200

        # Update with the field `efficiency`. Should succeed even with versions prior to v8.7
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={"efficiency": 97.0},
        )
        assert res.status_code == 200

        # =============================
        #  THERMAL CLUSTER DUPLICATION
        # =============================

        new_name = "Duplicate of Fr_Gas_Conventional"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/thermals/{fr_gas_conventional_id}",
            params={"newName": new_name},
        )
        assert res.status_code in {200, 201}, res.json()
        # asserts the config is the same
        duplicated_config = dict(fr_gas_conventional_cfg)
        duplicated_config["name"] = new_name
        duplicated_id = transform_name_to_id(new_name, lower=False)
        duplicated_config["id"] = duplicated_id
        # takes the update into account
        if version >= 860:
            duplicated_config["nox"] = 10
        if version >= 870:
            duplicated_config["efficiency"] = 97.0
        assert res.json() == duplicated_config

        # asserts the matrix has also been duplicated
        new_cluster_matrix_path = f"input/thermal/prepro/{area_id}/{duplicated_id.lower()}/data"
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": new_cluster_matrix_path})
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # =============================
        #  THERMAL CLUSTER VALIDATION
        # =============================

        # Everything is fine at the beginning
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}/validate"
        )
        assert res.status_code == 200
        assert res.json() is True

        # Modifies series matrix with wrong length (!= 8760)
        _upload_matrix(
            client,
            user_access_token,
            internal_study_id,
            f"input/thermal/series/{area_id}/{fr_gas_conventional_id.lower()}/series",
            pd.DataFrame(np.random.randint(0, 10, size=(4, 1))),
        )

        # Validation should fail
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}/validate"
        )
        assert res.status_code == 422
        obj = res.json()
        assert obj["exception"] == "WrongMatrixHeightError"
        assert obj["description"] == "The matrix series should have 8760 rows, currently: 4"

        # Update with the right length
        _upload_matrix(
            client,
            user_access_token,
            internal_study_id,
            f"input/thermal/series/{area_id}/{fr_gas_conventional_id.lower()}/series",
            pd.DataFrame(np.random.randint(0, 10, size=(8760, 4))),
        )

        # Validation should succeed again
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}/validate"
        )
        assert res.status_code == 200
        assert res.json() is True

        if version >= 870:
            # Adds a CO2Cost matrix with different columns size
            _upload_matrix(
                client,
                user_access_token,
                internal_study_id,
                f"input/thermal/series/{area_id}/{fr_gas_conventional_id.lower()}/CO2Cost",
                pd.DataFrame(np.random.randint(0, 10, size=(8760, 3))),
            )

            # Validation should fail
            res = client.get(
                f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}/validate"
            )
            assert res.status_code == 422
            obj = res.json()
            assert obj["exception"] == "MatrixWidthMismatchError"
            pattern = r".*'series'.*4.*'CO2Cost'.*3"
            assert re.match(pattern, obj["description"])

        # =============================
        #  THERMAL CLUSTER DELETION
        # =============================

        # Here is a Binding Constraint that references the thermal cluster.:
        bc_obj = {
            "name": "Binding Constraint",
            "enabled": True,
            "time_step": "hourly",
            "operator": "less",
            "terms": [
                {
                    "id": f"{area_id}.{fr_gas_conventional_id.lower()}",
                    "weight": 2,
                    "offset": 5,
                    "data": {"area": area_id, "cluster": fr_gas_conventional_id.lower()},
                }
            ],
            "comments": "New API",
        }
        matrix = np.random.randint(0, 1000, size=(8784, 3))
        if version < 870:
            bc_obj["values"] = matrix.tolist()
        else:
            bc_obj["lessTermMatrix"] = matrix.tolist()

        # noinspection SpellCheckingInspection
        res = client.post(f"/v1/studies/{internal_study_id}/bindingconstraints", json=bc_obj)
        assert res.status_code in {200, 201}, res.json()

        # verify that we can't delete the thermal cluster because it is referenced in a binding constraint
        res = client.request(
            "DELETE", f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=[fr_gas_conventional_id]
        )
        assert res.status_code == 403, res.json()
        description = res.json()["description"]
        assert all([elm in description for elm in [fr_gas_conventional, "binding constraint"]])
        assert res.json()["exception"] == "ReferencedObjectDeletionNotAllowed"

        # delete the binding constraint
        res = client.delete(f"/v1/studies/{internal_study_id}/bindingconstraints/{bc_obj['name']}")
        assert res.status_code == 200, res.json()

        # Now we can delete the thermal cluster
        res = client.request(
            "DELETE", f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=[fr_gas_conventional_id]
        )
        assert res.status_code == 204, res.json()

        # check that the binding constraint has been deleted
        # noinspection SpellCheckingInspection
        res = client.get(f"/v1/studies/{internal_study_id}/bindingconstraints")
        assert res.status_code == 200, res.json()
        assert len(res.json()) == 0

        # If the thermal cluster list is empty, the deletion should be a no-op.
        res = client.request("DELETE", f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal", json=[])
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # It's possible to delete multiple thermal clusters at once.
        # We can delete the two thermal clusters at once.
        other_cluster_id1 = "01_solar"
        other_cluster_id2 = "02_wind_on"
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal",
            json=[other_cluster_id1, other_cluster_id2],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # The list of thermal clusters should not contain the deleted ones.
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal")
        assert res.status_code == 200, res.json()
        deleted_clusters = [other_cluster_id1, other_cluster_id2, fr_gas_conventional_id]
        for cluster in res.json():
            assert transform_name_to_id(cluster["name"], lower=False) not in deleted_clusters

        # ===========================
        #  THERMAL CLUSTER ERRORS
        # ===========================

        # Check DELETE with the wrong value of `area_id`
        bad_area_id = "bad_area"
        res = client.request(
            "DELETE",
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/thermal",
            json=[fr_gas_conventional_id],
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
            "DELETE", f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal", json=[fr_gas_conventional_id]
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check GET with wrong `area_id`
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/thermal/{fr_gas_conventional_id}"
        )
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check GET with wrong `study_id`
        res = client.get(f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}")
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `study_id`
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal",
            json={"name": fr_gas_conventional, "group": "Battery"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `area_id`
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/thermal",
            json={
                "name": fr_gas_conventional,
                "group": "Oil",
                "unitCount": 1,
                "nominalCapacity": 120.0,
                "minStablePower": 60.0,
                "co2": 0.77,
                "marginalCost": 186.664,
                "startupCost": 4800.0,
                "marketBidCost": 186.664,
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
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal",
            json={"name": fr_gas_conventional, "group": "GroupFoo"},
        )
        assert res.status_code == 200, res.json()
        obj = res.json()
        # If a group is not found, return the default group ('OTHER1' by default).
        assert obj["group"] == "other 1"

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={
                "group": "Oil",
                "unitCount": 1,
                "nominalCapacity": 120.0,
                "minStablePower": 60.0,
                "co2": 0.77,
                "marginalCost": 186.664,
                "startupCost": 4800.0,
                "marketBidCost": 186.664,
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
            f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/thermal/{bad_cluster_id}",
            json={
                "group": "Oil",
                "unitCount": 1,
                "nominalCapacity": 120.0,
                "minStablePower": 60.0,
                "co2": 0.77,
                "marginalCost": 186.664,
                "startupCost": 4800.0,
                "marketBidCost": 186.664,
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_cluster_id in description
        assert re.search(re.escape("'bad_cluster' not found"), description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `study_id`
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            json={
                "group": "Oil",
                "unitCount": 1,
                "nominalCapacity": 120.0,
                "minStablePower": 60.0,
                "co2": 0.77,
                "marginalCost": 186.664,
                "startupCost": 4800.0,
                "marketBidCost": 186.664,
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_study_id in description

        # Cannot duplicate a fake cluster
        unknown_id = "unknown"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/thermals/{unknown_id}", params={"newName": "duplicate"}
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        assert f"'{unknown_id}' not found" in obj["description"]
        assert obj["exception"] == "ThermalClusterNotFound"

        # Cannot duplicate with an existing id
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/thermals/{duplicated_id}",
            params={"newName": new_name.upper()},  # different case but same ID
        )
        assert res.status_code == 409, res.json()
        obj = res.json()
        description = obj["description"]
        assert new_name.upper() in description
        assert obj["exception"] == "DuplicateThermalCluster"

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
        In this test, we want to check that thermal clusters can be managed
        in the context of a "variant" study.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Create an area
        area_name = "France"
        res = client.post(f"/v1/studies/{variant_id}/areas", json={"name": area_name, "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()
        area_cfg = res.json()
        area_id = area_cfg["id"]

        # Create a thermal cluster
        cluster_name = "Th1"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/clusters/thermal",
            json={
                "name": cluster_name,
                "group": "Nuclear",
                "unitCount": 13,
                "nominalCapacity": 42500,
                "marginalCost": 0.1,
            },
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_id: str = res.json()["id"]

        # Update the thermal cluster
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/clusters/thermal/{cluster_id}", json={"marginalCost": 0.2}
        )
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["marginalCost"] == 0.2

        # Update the prepro matrix
        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/thermal/prepro/{area_id}/{cluster_id.lower()}/data"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(f"/v1/studies/{variant_id}/commands", json=[{"action": "replace_matrix", "args": args}])
        assert res.status_code in {200, 201}, res.json()

        # Duplicate the thermal cluster
        new_name = "Th2"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/thermals/{cluster_id}", params={"newName": new_name}
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["name"] == new_name
        new_id = cluster_cfg["id"]

        # Check that the duplicate has the right properties
        res = client.get(f"/v1/studies/{variant_id}/areas/{area_id}/clusters/thermal/{new_id}")
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["group"] == "nuclear"
        assert cluster_cfg["unitCount"] == 13
        assert cluster_cfg["nominalCapacity"] == 42500
        assert cluster_cfg["marginalCost"] == 0.2

        # Check that the duplicate has the right matrix
        new_cluster_matrix_path = f"input/thermal/prepro/{area_id}/{new_id.lower()}/data"
        res = client.get(f"/v1/studies/{variant_id}/raw", params={"path": new_cluster_matrix_path})
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # Delete the thermal cluster
        # usage of request instead of delete as httpx doesn't support delete with a payload anymore.
        res = client.request(
            method="DELETE", url=f"/v1/studies/{variant_id}/areas/{area_id}/clusters/thermal", json=[cluster_id]
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
            "create_cluster",
            "update_thermal_cluster",
            "replace_matrix",
            "create_cluster",
            "replace_matrix",
            "remove_cluster",
        ]

    def test_thermal_cluster_deletion(self, client: TestClient, user_access_token: str, internal_study_id: str) -> None:
        """
        Test that creating a thermal cluster with invalid properties raises a validation error.
        """

        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create an area "area_1" in the study
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas",
            json={
                "name": "area_1",
                "type": "AREA",
                "metadata": {"country": "FR"},
            },
        )
        assert res.status_code == 200, res.json()

        # Create an area "area_2" in the study
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas",
            json={
                "name": "area_2",
                "type": "AREA",
                "metadata": {"country": "DE"},
            },
        )
        assert res.status_code == 200, res.json()

        # Create an area "area_3" in the study
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas",
            json={
                "name": "area_3",
                "type": "AREA",
                "metadata": {"country": "ES"},
            },
        )
        assert res.status_code == 200, res.json()

        # Create a thermal cluster in the study for area_1
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/area_1/clusters/thermal",
            json={
                "name": "cluster_1",
                "group": "Nuclear",
                "unitCount": 13,
                "nominalCapacity": 42500,
                "marginalCost": 0.1,
            },
        )
        assert res.status_code == 200, res.json()

        # Create a thermal cluster in the study for area_2
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/area_2/clusters/thermal",
            json={
                "name": "cluster_2",
                "group": "Nuclear",
                "unitCount": 13,
                "nominalCapacity": 42500,
                "marginalCost": 0.1,
            },
        )
        assert res.status_code == 200, res.json()

        # Create a thermal cluster in the study for area_3
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/area_3/clusters/thermal",
            json={
                "name": "cluster_3",
                "group": "Nuclear",
                "unitCount": 13,
                "nominalCapacity": 42500,
                "marginalCost": 0.1,
            },
        )
        assert res.status_code == 200, res.json()

        # add a binding constraint that references the thermal cluster in area_1
        bc_obj = {
            "name": "bc_1",
            "enabled": True,
            "time_step": "hourly",
            "operator": "less",
            "terms": [
                {
                    "id": "area_1.cluster_1",
                    "weight": 2,
                    "offset": 5,
                    "data": {"area": "area_1", "cluster": "cluster_1"},
                }
            ],
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/bindingconstraints",
            json=bc_obj,
        )
        assert res.status_code == 200, res.json()

        # add a binding constraint that references the thermal cluster in area_2
        bc_obj = {
            "name": "bc_2",
            "enabled": True,
            "time_step": "hourly",
            "operator": "less",
            "terms": [
                {
                    "id": "area_2.cluster_2",
                    "weight": 2,
                    "offset": 5,
                    "data": {"area": "area_2", "cluster": "cluster_2"},
                }
            ],
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/bindingconstraints",
            json=bc_obj,
        )
        assert res.status_code == 200, res.json()

        # check that deleting the thermal cluster in area_1 fails
        # usage of request instead of delete as httpx doesn't support delete with a payload anymore.
        res = client.request(
            method="DELETE", url=f"/v1/studies/{internal_study_id}/areas/area_1/clusters/thermal", json=["cluster_1"]
        )
        assert res.status_code == 403, res.json()

        # now delete the binding constraint that references the thermal cluster in area_1
        res = client.delete(
            f"/v1/studies/{internal_study_id}/bindingconstraints/bc_1",
        )
        assert res.status_code == 200, res.json()

        # check that deleting the thermal cluster in area_1 succeeds
        res = client.request(
            method="DELETE", url=f"/v1/studies/{internal_study_id}/areas/area_1/clusters/thermal", json=["cluster_1"]
        )
        assert res.status_code == 204, res.json()

        # check that deleting the thermal cluster in area_2 fails
        res = client.request(
            method="DELETE", url=f"/v1/studies/{internal_study_id}/areas/area_2/clusters/thermal", json=["cluster_2"]
        )
        assert res.status_code == 403, res.json()

        # now delete the binding constraint that references the thermal cluster in area_2
        res = client.delete(
            f"/v1/studies/{internal_study_id}/bindingconstraints/bc_2",
        )
        assert res.status_code == 200, res.json()

        # check that deleting the thermal cluster in area_2 succeeds
        res = client.request(
            method="DELETE", url=f"/v1/studies/{internal_study_id}/areas/area_2/clusters/thermal", json=["cluster_2"]
        )
        assert res.status_code == 204, res.json()

        # check that deleting the thermal cluster in area_3 succeeds
        res = client.request(
            method="DELETE", url=f"/v1/studies/{internal_study_id}/areas/area_3/clusters/thermal", json=["cluster_3"]
        )
        assert res.status_code == 204, res.json()
