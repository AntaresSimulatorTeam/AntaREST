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

        ## Upgrade study to version 860
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": 860},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        ## creation with default values (only mandatory properties specified)
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

        ## reading the properties of a short-term storage
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
        # check the updating
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

        ## deletion of short-term storages
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/st-storage/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        # todo: check the removal
        # res = client.get(
        #     f"/v1/studies/{study_id}/areas/{area_id}/st-storage",
        #     headers={"Authorization": f"Bearer {user_access_token}"},
        # )
        # res.raise_for_status()
        # assert res.json() == []
