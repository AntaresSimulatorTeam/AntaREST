import json

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from tests.integration.utils import wait_task_completion  #


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

        # creation with default values (only mandatory properties specified)
        area_id = transform_name_to_id("FR")
        siemens_battery = "Siemens Battery"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        res.raise_for_status()
        siemens_battery_id = res.json()
        assert siemens_battery_id == transform_name_to_id(siemens_battery)

        # reading the properties of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert res.json() == {
            "efficiency": 1.0,
            "group": "Battery",
            "id": siemens_battery_id,
            "initialLevel": 0.0,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "name": siemens_battery,
            "reservoirCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
        }

        # reading the matrix of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}/inflows",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        matrix = res.json()
        array = np.array(matrix["data"], dtype=np.float64)
        assert array.all() == 0

        # todo: reading the list of short-term storages
        # res = client.get(
        #     f"/v1/studies/{study_id}/areas/{area_id}/st-storage",
        #     headers={"Authorization": f"Bearer {user_access_token}"},
        # )
        # res.raise_for_status()
        # assert res.json() == [
        #     {
        #         "efficiency": 1.0,
        #         "group": "Battery",
        #         "id": siemens_battery_id,
        #         "initialLevel": 0.0,
        #         "initialLevelOptim": False,
        #         "injectionNominalCapacity": 0.0,
        #         "name": siemens_battery,
        #         "reservoirCapacity": 0.0,
        #         "withdrawalNominalCapacity": 0.0,
        #     }
        # ]

        # updating properties
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.raise_for_status()
        assert res.status_code == 200
        assert json.loads(res.text) == {
            "efficiency": 1.0,
            "group": "Battery",
            "id": "siemens battery",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": 2350,
        }

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert res.json() == {
            "efficiency": 1.0,
            "group": "Battery",
            "id": siemens_battery_id,
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": 2350,
        }

        # todo: updating a matrix

        # deletion of short-term storages
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert res.status_code == 200
        assert res.text == "null"

        #  Check the removal
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert res.status_code.value == 404
        assert (
            json.loads(res.text)["description"]
            == f"Error in the study '{study_id}', the short-term storage configuration of area '{area_id}' is "
            f"invalid: fields of storage '{siemens_battery_id}' not found"
        )
        assert (
            json.loads(res.text)["exception"] == "STStorageFieldsNotFoundError"
        )

        # Check delete with the wrong value of area_id
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}foo/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 404
        assert (
            json.loads(res.text)["description"]
            == f"Unexpected exception occurred when trying to apply command CommandName.REMOVE_ST_STORAGE: '{area_id}foo' not a child of InputSTStorageClusters"
        )
        assert json.loads(res.text)["exception"] == "CommandApplicationError"

        # Check delete with the wrong value of study_id
        res = client.delete(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        # res.raise_for_status()
        assert res.status_code.value == 404
        assert json.loads(res.text)["description"] == study_id + "foo"
        assert json.loads(res.text)["exception"] == "StudyNotFoundError"

        # Check get with wrong area_id

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}foo/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert res.status_code.value == 404
        assert (
            json.loads(res.text)["description"]
            == f"'{area_id}foo' not a child of InputSTStorageClusters"
        )
        assert json.loads(res.text)["exception"] == "ChildNotFoundError"

        # Check get with wrong study_id

        res = client.get(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code.value == 404
        assert json.loads(res.text)["description"] == f"{study_id}foo"
        assert json.loads(res.text)["exception"] == "StudyNotFoundError"

        # Check post with wrong study_id
        res = client.post(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code.value == 404
        assert json.loads(res.text)["description"] == f"{study_id}foo"
        assert json.loads(res.text)["exception"] == "StudyNotFoundError"

        # Check post with wrong area_id
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}foo/st-storage",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 404

        assert (
            json.loads(res.text)["description"]
            == f"Area '{area_id}foo' does not exist in the study configuration."
        )
        assert json.loads(res.text)["exception"] == "CommandApplicationError"

        # Check post with wrong group
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}foo/st-storage",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Batteryfoo"},
        )
        assert res.status_code == 422

        assert (
            json.loads(res.text)["description"]
            == "value is not a valid enumeration member; permitted: 'PSP_open', "
            "'PSP_closed', 'Pondage', 'Battery', 'Other1', 'Other2', 'Other3', 'Other4', 'Other5'"
        )
        assert json.loads(res.text)["body"] == {
            "name": "Siemens Battery",
            "group": "Batteryfoo",
        }
        assert json.loads(res.text)["exception"] == "RequestValidationError"

        # Check the put with the wrong area_id
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}foo/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code.value == 404
        assert (
            json.loads(res.text)["description"]
            == f"'{area_id}foo' not a child of InputSTStorageClusters"
        )
        assert json.loads(res.text)["exception"] == "ChildNotFoundError"

        # Check the put with the wrong siemens_battery_id
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code.value == 404
        assert (
            json.loads(res.text)["description"]
            == f"Error in the study '{study_id}', the short-term storage configuration of area '{area_id}' is "
            f"invalid: fields of storage '{siemens_battery_id}' not found"
        )

        # Check the put with the wrong study_id
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.status_code.value == 404
        assert json.loads(res.text)["description"] == study_id + "foo"
        assert json.loads(res.text)["exception"] == "StudyNotFoundError"

        # Check the put with the wrong efficiency
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 2.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.status_code == 422
        assert (
            json.loads(res.text)["description"]
            == "ensure this value is less than or equal to 1"
        )
        assert json.loads(res.text)["exception"] == "RequestValidationError"
        assert json.loads(res.text)["body"] == {
            "efficiency": 2.0,
            "group": "Battery",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": 2350,
        }

        # Check the put with the wrong initialLevel
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": -1,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.status_code == 422
        assert (
            json.loads(res.text)["description"]
            == "ensure this value is greater than or equal to 0"
        )
        assert json.loads(res.text)["exception"] == "RequestValidationError"
        assert json.loads(res.text)["body"] == {
            "efficiency": 1.0,
            "group": "Battery",
            "initialLevel": -1,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": 2350,
        }

        # Check the put with the wrong injectionNominalCapacity
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": -1,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.status_code == 422
        assert (
            json.loads(res.text)["description"]
            == "ensure this value is greater than or equal to 0"
        )
        assert json.loads(res.text)["exception"] == "RequestValidationError"
        assert json.loads(res.text)["body"] == {
            "efficiency": 1.0,
            "group": "Battery",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": -1,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": 2350,
        }

        # Check the put with the wrong reservoirCapacity
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": -1,
                "withdrawalNominalCapacity": 2350,
            },
        )
        res.status_code == 422
        assert (
            json.loads(res.text)["description"]
            == "ensure this value is greater than or equal to 0"
        )
        assert json.loads(res.text)["exception"] == "RequestValidationError"
        assert json.loads(res.text)["body"] == {
            "efficiency": 1.0,
            "group": "Battery",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": -1,
            "withdrawalNominalCapacity": 2350,
        }

        # Check the put with the wrong withdrawalNominalCapacity
        res = client.put(
            f"/v1/studies/{study_id}foo/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "group": "Battery",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": -1,
            },
        )
        res.status_code == 422
        assert (
            json.loads(res.text)["description"]
            == "ensure this value is greater than or equal to 0"
        )
        assert json.loads(res.text)["exception"] == "RequestValidationError"
        assert json.loads(res.text)["body"] == {
            "efficiency": 1.0,
            "group": "Battery",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 2450,
            "name": "New Siemens Battery",
            "reservoirCapacity": 2500,
            "withdrawalNominalCapacity": -1,
        }
