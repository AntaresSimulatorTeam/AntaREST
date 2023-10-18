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
  - `StudyPermissionType.DELETE`: user/bot has no permission to manage clusters,
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
import json
import re

import pytest
from starlette.testclient import TestClient

from antarest.core.utils.string import to_camel_case
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import Thermal860Properties, ThermalProperties

DEFAULT_PROPERTIES = json.loads(ThermalProperties(name="Dummy").json())
DEFAULT_PROPERTIES = {to_camel_case(k): v for k, v in DEFAULT_PROPERTIES.items() if k != "name"}

DEFAULT_860_PROPERTIES = json.loads(Thermal860Properties(name="Dummy").json())
DEFAULT_860_PROPERTIES = {to_camel_case(k): v for k, v in DEFAULT_860_PROPERTIES.items() if k != "name"}

# noinspection SpellCheckingInspection
EXISTING_CLUSTERS = [
    {
        "co2": 0.0,
        "enabled": True,
        "fixedCost": 0.0,
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
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
        "genTs": "use global parameter",
        "group": "Other 1",
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
        "nh3": None,
        "nmvoc": None,
        "nominalCapacity": 1000000.0,
        "nox": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "pm10": None,
        "pm25": None,
        "pm5": None,
        "so2": None,
        "spinning": 0.0,
        "spreadCost": 0.0,
        "startupCost": 0.0,
        "unitCount": 1,
        "volatilityForced": 0.0,
        "volatilityPlanned": 0.0,
    },
]


@pytest.mark.unit_test
class TestThermal:
    def test_lifecycle(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        # =============================
        #  THERMAL CLUSTER CREATION
        # =============================

        area_id = transform_name_to_id("FR")
        fr_gas_conventional = "FR_Gas conventional"

        # Un attempt to create a thermal cluster without name
        # should raise a validation error (other properties are optional).
        # Un attempt to create a thermal cluster with an empty name
        # or an invalid name should also raise a validation error.
        attempts = [{}, {"name": ""}, {"name": "!??"}]
        for attempt in attempts:
            res = client.post(
                f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
                headers={"Authorization": f"Bearer {user_access_token}"},
                json=attempt,
            )
            assert res.status_code == 422, res.json()
            assert res.json()["exception"] in {"ValidationError", "RequestValidationError"}, res.json()

        # We can create a thermal cluster with the following properties:
        fr_gas_conventional_props = {
            **DEFAULT_PROPERTIES,
            "name": fr_gas_conventional,
            "group": "Gas",
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=fr_gas_conventional_props,
        )
        assert res.status_code == 200, res.json()
        fr_gas_conventional_id = res.json()["id"]
        assert fr_gas_conventional_id == transform_name_to_id(fr_gas_conventional, lower=False)
        # noinspection SpellCheckingInspection
        fr_gas_conventional_cfg = {
            **fr_gas_conventional_props,
            "id": fr_gas_conventional_id,
            "nh3": None,
            "nmvoc": None,
            "nox": None,
            "op1": None,
            "op2": None,
            "op3": None,
            "op4": None,
            "op5": None,
            "pm10": None,
            "pm25": None,
            "pm5": None,
            "so2": None,
        }
        assert res.json() == fr_gas_conventional_cfg

        # reading the properties of a thermal cluster
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # =============================
        #  THERMAL CLUSTER MATRICES
        # =============================

        # TODO: add unit tests for thermal cluster matrices

        # ==================================
        #  THERMAL CLUSTER LIST / GROUPS
        # ==================================

        # Reading the list of thermal clusters
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == EXISTING_CLUSTERS + [fr_gas_conventional_cfg]

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
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

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # ===========================
        #  THERMAL CLUSTER UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=bad_properties,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "ValidationError", res.json()

        # The thermal cluster properties should not have been updated.
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == fr_gas_conventional_cfg

        # =============================
        #  THERMAL CLUSTER DELETION
        # =============================

        # To delete a thermal cluster, we need to provide its ID.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_gas_conventional_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # If the thermal cluster list is empty, the deletion should be a no-op.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # It's possible to delete multiple thermal clusters at once.
        # We can delete the two thermal clusters at once.
        other_cluster_id1 = "01_solar"
        other_cluster_id2 = "02_wind_on"
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[other_cluster_id1, other_cluster_id2],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # The list of thermal clusters should be empty.
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        expected = [
            c
            for c in EXISTING_CLUSTERS
            if transform_name_to_id(c["name"], lower=False) not in [other_cluster_id1, other_cluster_id2]
        ]
        assert res.json() == expected

        # ===========================
        #  THERMAL CLUSTER ERRORS
        # ===========================

        # Check DELETE with the wrong value of `area_id`
        bad_area_id = "bad_area"
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
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
            "DELETE",
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[fr_gas_conventional_id],
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check GET with wrong `area_id`
        res = client.get(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check GET with wrong `study_id`
        res = client.get(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `study_id`
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": fr_gas_conventional, "group": "Battery"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `area_id`
        res = client.post(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
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
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": fr_gas_conventional, "group": "GroupFoo"},
        )
        assert res.status_code == 200, res.json()
        obj = res.json()
        # If a group is not found, return the default group ('OTHER1' by default).
        assert obj["group"] == "Other 1"

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/clusters/thermal/{fr_gas_conventional_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
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
        assert re.search(r"not a child of ", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `cluster_id`
        bad_cluster_id = "bad_cluster"
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/clusters/thermal/{bad_cluster_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
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
            headers={"Authorization": f"Bearer {user_access_token}"},
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
