import json
import re
from unittest.mock import ANY

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.business.areas.st_storage_management import STStorageOutput
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageConfig
from tests.integration.utils import wait_task_completion

DEFAULT_CONFIG = json.loads(STStorageConfig(id="dummy", name="dummy").json(by_alias=True, exclude={"id", "name"}))

DEFAULT_PROPERTIES = json.loads(STStorageOutput(name="dummy").json(by_alias=True, exclude={"id", "name"}))


# noinspection SpellCheckingInspection
@pytest.mark.unit_test
class TestSTStorage:
    # noinspection GrazieInspection
    """
    Test the end points related to short term storage.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_lifecycle__nominal(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        The purpose of this integration test is to test the endpoints
        related to short-term storage management.

        To ensure functionality, the test needs to be performed on a study
        in version 860 or higher. That's why we will upgrade the "STA-mini"
        study, which is in an older version.

        We will test the creation of multiple short-term storages.

        We will test reading the properties of a short-term storage
        and reading a matrix from a short-term storage.

        We will test reading the list of short-term storages and
        verify that the list is properly ordered by group and name.

        We will test updating a short-term storage:

        - updating properties,
        - updating a matrix.

        We will test the deletion of short-term storages.
        """

        # Upgrade study to version 860
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": 860},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # =============================
        #  SHORT-TERM STORAGE CREATION
        # =============================

        area_id = transform_name_to_id("FR")
        siemens_battery = "Siemens Battery"

        # Un attempt to create a short-term storage without name
        # should raise a validation error (other properties are optional).
        # Un attempt to create a short-term storage with an empty name
        # or an invalid name should also raise a validation error.
        attempts = [{}, {"name": ""}, {"name": "!??"}]
        for attempt in attempts:
            res = client.post(
                f"/v1/studies/{study_id}/areas/{area_id}/storages",
                headers={"Authorization": f"Bearer {user_access_token}"},
                json=attempt,
            )
            assert res.status_code == 422, res.json()
            assert res.json()["exception"] in {"ValidationError", "RequestValidationError"}, res.json()

        # We can create a short-term storage with the following properties:
        siemens_properties = {
            **DEFAULT_PROPERTIES,
            "name": siemens_battery,
            "group": "Battery",
            "injectionNominalCapacity": 1450,
            "withdrawalNominalCapacity": 1350,
            "reservoirCapacity": 1500,
        }
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=siemens_properties,
        )
        assert res.status_code == 200, res.json()
        siemens_battery_id = res.json()["id"]
        assert siemens_battery_id == transform_name_to_id(siemens_battery)
        siemens_config = {**siemens_properties, "id": siemens_battery_id}
        assert res.json() == siemens_config

        # reading the properties of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_config

        # =============================
        #  SHORT-TERM STORAGE MATRICES
        # =============================

        # updating the matrix of a short-term storage
        array = np.random.rand(8760, 1) * 1000
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/series/inflows",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            },
        )
        assert res.status_code == 200, res.json()
        assert res.json() is None

        # reading the matrix of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/series/inflows",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        matrix = res.json()
        actual = np.array(matrix["data"], dtype=np.float64)
        assert actual.all() == array.all()

        # validating the matrices of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/validate",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() is True

        # ==================================
        #  SHORT-TERM STORAGE LIST / GROUPS
        # ==================================

        # Reading the list of short-term storages
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == [siemens_config]

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
            },
        )
        assert res.status_code == 200, res.json()
        siemens_config = {
            **siemens_config,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
        }
        assert res.json() == siemens_config

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_config

        # ===========================
        #  SHORT-TERM STORAGE UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "initialLevel": 0.59,
                "reservoirCapacity": 0,
            },
        )
        siemens_config = {
            **siemens_config,
            "initialLevel": 0.59,
            "reservoirCapacity": 0,
        }
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_config

        # An attempt to update the `efficiency` property with an invalid value
        # should raise a validation error.
        # The `efficiency` property must be a float between 0 and 1.
        bad_properties = {"efficiency": 2.0}
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=bad_properties,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "RequestValidationError", res.json()

        # The short-term storage properties should not have been updated.
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_config

        # =============================
        #  SHORT-TERM STORAGE DELETION
        # =============================

        # To delete a short-term storage, we need to provide its ID.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # If the short-term storage list is empty, the deletion should be a no-op.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # It's possible to delete multiple short-term storages at once.
        # In the following example, we will create two short-term storages:
        siemens_properties = {
            "name": siemens_battery,
            "group": "Battery",
            "injectionNominalCapacity": 1450,
            "withdrawalNominalCapacity": 1350,
            "reservoirCapacity": 1500,
            "efficiency": 0.90,
            "initialLevel": 0.2,
            "initialLevelOptim": False,
        }
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=siemens_properties,
        )
        assert res.status_code == 200, res.json()
        siemens_battery_id = res.json()["id"]

        # Create another short-term storage: "Grand'Maison"
        grand_maison = "Grand'Maison"
        grand_maison_properties = {
            "name": grand_maison,
            "group": "PSP_closed",
            "injectionNominalCapacity": 1500,
            "withdrawalNominalCapacity": 1800,
            "reservoirCapacity": 20000,
            "efficiency": 0.78,
            "initialLevel": 1,
        }
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=grand_maison_properties,
        )
        assert res.status_code == 200, res.json()
        grand_maison_id = res.json()["id"]

        # We can check that we have 2 short-term storages in the list.
        # Reading the list of short-term storages
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        siemens_config = {**DEFAULT_PROPERTIES, **siemens_properties, "id": siemens_battery_id}
        grand_maison_config = {**DEFAULT_PROPERTIES, **grand_maison_properties, "id": grand_maison_id}
        assert res.json() == [siemens_config, grand_maison_config]

        # We can delete the two short-term storages at once.
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id, grand_maison_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text in {"", "null"}  # Old FastAPI versions return 'null'.

        # The list of short-term storages should be empty.
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == []

        # ===========================
        #  SHORT-TERM STORAGE ERRORS
        # ===========================

        # Check delete with the wrong value of `area_id`
        bad_area_id = "bad_area"
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(
            r"CommandName.REMOVE_ST_STORAGE",
            description,
            flags=re.IGNORECASE,
        )

        # Check delete with the wrong value of `study_id`
        bad_study_id = "bad_study"
        res = client.request(
            "DELETE",
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check get with wrong `area_id`
        res = client.get(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check get with wrong `study_id`
        res = client.get(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `study_id`
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `area_id`
        res = client.post(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"Area ", description, flags=re.IGNORECASE)
        assert re.search(r"does not exist ", description, flags=re.IGNORECASE)

        # Check POST with wrong `group`
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "GroupFoo"},
        )
        assert res.status_code == 422, res.json()
        obj = res.json()
        description = obj["description"]
        assert re.search(r"not a valid enumeration member", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"efficiency": 1.0},
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"not a child of ", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `storage_id`
        bad_storage_id = "bad_storage"
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{bad_storage_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"efficiency": 1.0},
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_storage_id in description
        assert re.search(r"fields of storage", description, flags=re.IGNORECASE)
        assert re.search(r"not found", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `study_id`
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"efficiency": 1.0},
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_study_id in description

    def test__default_values(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        """
        The purpose of this integration test is to test the default values of
        the properties of a short-term storage.

        Given a new study with an area "FR", at least in version 860,
        When I create a short-term storage with a name "Tesla Battery", with the default values,
        Then the short-term storage is created with initialLevel = 0.0, and initialLevelOptim = False.
        """
        # Create a new study in version 860 (or higher)
        res = client.post(
            "/v1/studies",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": "MyStudy", "version": 860},
        )
        assert res.status_code in {200, 201}, res.json()
        study_id = res.json()

        # Create a new area named "FR"
        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": "FR", "type": "AREA"},
        )
        assert res.status_code in {200, 201}, res.json()
        area_id = res.json()["id"]

        # Create a new short-term storage named "Tesla Battery"
        tesla_battery = "Tesla Battery"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": tesla_battery, "group": "Battery"},
        )
        assert res.status_code == 200, res.json()
        tesla_battery_id = res.json()["id"]
        tesla_config = {**DEFAULT_PROPERTIES, "id": tesla_battery_id, "name": tesla_battery, "group": "Battery"}
        assert res.json() == tesla_config

        # Use the Debug mode to make sure that the initialLevel and initialLevelOptim properties
        # are properly set in the configuration file.
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"path": f"input/st-storage/clusters/{area_id}/list/{tesla_battery_id}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {**DEFAULT_CONFIG, "name": tesla_battery, "group": "Battery"}
        assert actual == expected

        # We want to make sure that the default properties are applied to a study variant.
        # We want to make sure that updating the initialLevel property is taken into account
        # in the variant commands.

        # Create a variant of the study
        res = client.post(
            f"/v1/studies/{study_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": "MyVariant"},
        )
        assert res.status_code in {200, 201}, res.json()
        variant_id = res.json()

        # Create a new short-term storage named "Siemens Battery"
        siemens_battery = "Siemens Battery"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(
            f"/v1/studies/{variant_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 1
        actual = commands[0]
        expected = {
            "id": ANY,
            "action": "create_st_storage",
            "args": {
                "area_id": "fr",
                "parameters": {**DEFAULT_CONFIG, "name": siemens_battery, "group": "Battery"},
                "pmax_injection": ANY,
                "pmax_withdrawal": ANY,
                "lower_rule_curve": ANY,
                "upper_rule_curve": ANY,
                "inflows": ANY,
            },
            "version": 1,
        }
        assert actual == expected

        # Update the initialLevel property of the "Siemens Battery" short-term storage to 0.5
        siemens_battery_id = transform_name_to_id(siemens_battery)
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"initialLevel": 0.5},
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(
            f"/v1/studies/{variant_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 2
        actual = commands[1]
        expected = {
            "id": ANY,
            "action": "update_config",
            "args": {
                "data": "0.5",
                "target": "input/st-storage/clusters/fr/list/siemens battery/initiallevel",
            },
            "version": 1,
        }
        assert actual == expected

        # Update the initialLevel property of the "Siemens Battery" short-term storage back to 0
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"initialLevel": 0.0, "injectionNominalCapacity": 1600},
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(
            f"/v1/studies/{variant_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 3
        actual = commands[2]
        expected = {
            "id": ANY,
            "action": "update_config",
            "args": [
                {
                    "data": "1600.0",
                    "target": "input/st-storage/clusters/fr/list/siemens battery/injectionnominalcapacity",
                },
                {
                    "data": "0.0",
                    "target": "input/st-storage/clusters/fr/list/siemens battery/initiallevel",
                },
            ],
            "version": 1,
        }
        assert actual == expected

        # Use the Debug mode to make sure that the initialLevel and initialLevelOptim properties
        # are properly set in the configuration file.
        res = client.get(
            f"/v1/studies/{variant_id}/raw",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"path": f"input/st-storage/clusters/{area_id}/list/{siemens_battery_id}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            **DEFAULT_CONFIG,
            "name": siemens_battery,
            "group": "Battery",
            "injectionnominalcapacity": 1600,
            "initiallevel": 0.0,
        }
        assert actual == expected
