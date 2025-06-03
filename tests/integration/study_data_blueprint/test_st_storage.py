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

import re
import typing as t
from unittest.mock import ANY

import numpy as np
import pytest
from antares.study.version import StudyVersion
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageFileData, parse_st_storage
from tests.integration.utils import wait_task_completion

_ST_STORAGE_860 = parse_st_storage(STUDY_VERSION_8_6, data={"name": "dummy"})
_ST_STORAGE_880 = parse_st_storage(STUDY_VERSION_8_8, data={"name": "dummy"})

ST_STORAGE_DICT_860 = _ST_STORAGE_860.model_dump(mode="json", by_alias=True, exclude={"id", "name"})
ST_STORAGE_DICT_880 = _ST_STORAGE_880.model_dump(mode="json", by_alias=True, exclude={"id", "name"})

ST_STORAGE_INI_860 = STStorageFileData.from_model(_ST_STORAGE_860).model_dump(
    mode="json", by_alias=True, exclude={"name"}, exclude_none=True
)
ST_STORAGE_INI_880 = STStorageFileData.from_model(_ST_STORAGE_880).model_dump(
    mode="json", by_alias=True, exclude={"name"}, exclude_none=True
)


# noinspection SpellCheckingInspection
@pytest.mark.unit_test
class TestSTStorage:
    # noinspection GrazieInspection
    """
    Test the end points related to short term storage.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    @pytest.mark.parametrize(
        "study_version, default_output",
        [
            pytest.param(STUDY_VERSION_8_6, ST_STORAGE_DICT_860, id="860"),
            pytest.param(STUDY_VERSION_8_8, ST_STORAGE_DICT_880, id="880"),
        ],
    )
    def test_lifecycle__nominal(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
        study_type: str,
        study_version: StudyVersion,
        default_output: t.Dict[str, t.Any],
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

        # =============================
        #  SET UP
        # =============================
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Upgrade study to version 860 or above
        res = client.put(f"/v1/studies/{internal_study_id}/upgrade", params={"target_version": f"{study_version:ddd}"})
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # Copies the study, to convert it into a managed one.
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            params={"study_name": "default", "with_outputs": False, "use_task": False},
        )
        assert res.status_code == 201, res.json()
        internal_study_id = res.json()

        if study_type == "variant":
            # Create Variant
            res = client.post(f"/v1/studies/{internal_study_id}/variants", params={"name": "Variant 1"})
            assert res.status_code in {200, 201}, res.json()
            internal_study_id = res.json()

        # =============================
        #  SHORT-TERM STORAGE CREATION
        # =============================

        area_id = transform_name_to_id("FR")
        siemens_battery = "Siemens Battery"
        storage_url = f"/v1/studies/{internal_study_id}/areas/{area_id}/storages"

        # An attempt to create a short-term storage without name
        # should raise a validation error (other properties are optional).
        # The same goes for empty or invalid names
        attempts = [{}, {"name": ""}, {"name": "!??"}]
        for attempt in attempts:
            res = client.post(storage_url, json=attempt)
            assert res.status_code == 422, res.json()
            assert res.json()["exception"] in {"ValidationError", "RequestValidationError"}, res.json()

        # We can create a short-term storage with the following properties.
        # Unfilled properties will be set to their default values.
        siemens_properties = {
            "name": siemens_battery,
            "group": "battery",
            "injectionNominalCapacity": 1450,
            "withdrawalNominalCapacity": 1350,
            "reservoirCapacity": 1500,
        }
        res = client.post(storage_url, json=siemens_properties)
        assert res.status_code == 200, res.json()
        siemens_battery_id = res.json()["id"]
        assert siemens_battery_id == transform_name_to_id(siemens_battery)
        siemens_output = {**default_output, **siemens_properties, "id": siemens_battery_id}
        assert res.json() == siemens_output

        # reading the properties of a short-term storage
        res = client.get(f"{storage_url}/{siemens_battery_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_output

        # =============================
        #  SHORT-TERM STORAGE MATRICES
        # =============================

        # updating the matrix of a short-term storage
        array = np.random.randint(0, 1000, size=(8760, 1))
        array_list = array.tolist()
        matrix_path = f"input/st-storage/series/{area_id}/{siemens_battery_id}/inflows"
        res = client.post(f"/v1/studies/{internal_study_id}/raw?path={matrix_path}", json=array_list)
        assert res.status_code == 200, res.json()

        # reading the matrix of a short-term storage
        res = client.get(f"/v1/studies/{internal_study_id}/raw?path={matrix_path}")
        assert res.status_code == 200, res.json()
        matrix = res.json()
        actual = np.array(matrix["data"], dtype=np.float64)
        assert actual.all() == array.all()

        # ==================================
        #  SHORT-TERM STORAGE LIST / GROUPS
        # ==================================

        # Reading the list of short-term storages
        res = client.get(storage_url)
        assert res.status_code == 200, res.json()
        assert res.json() == [siemens_output]

        # updating properties
        res = client.patch(
            f"{storage_url}/{siemens_battery_id}",
            json={
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
            },
        )
        # Ensures we're still able to process a name here (legacy) but we don't update it
        assert res.status_code == 200, res.json()
        siemens_output = {**siemens_output, "reservoirCapacity": 2500}
        assert res.json() == siemens_output

        res = client.get(f"{storage_url}/{siemens_battery_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_output

        # ===========================
        #  SHORT-TERM STORAGE UPDATE
        # ===========================

        # updating properties
        res = client.patch(
            f"{storage_url}/{siemens_battery_id}",
            json={"initialLevel": 0.59, "reservoirCapacity": 0},
        )
        siemens_output = {**siemens_output, "initialLevel": 0.59, "reservoirCapacity": 0}
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_output

        # An attempt to update the `efficiency` property with an invalid value
        # should raise a validation error.
        # The `efficiency` property must be a float between 0 and 1.
        bad_properties = {"efficiency": 2.0}
        res = client.patch(f"{storage_url}/{siemens_battery_id}", json=bad_properties)
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "RequestValidationError", res.json()

        # The short-term storage properties should not have been updated.
        res = client.get(f"{storage_url}/{siemens_battery_id}")
        assert res.status_code == 200, res.json()
        assert res.json() == siemens_output

        # =============================
        #  SHORT-TERM STORAGE DUPLICATION
        # =============================

        new_name = "Duplicate of Siemens"
        res = client.post(
            f"{storage_url}/{siemens_battery_id}",
            params={"newName": new_name},
        )
        assert res.status_code in {200, 201}, res.json()
        # asserts the config is the same
        duplicated_output = dict(siemens_output)
        duplicated_output["name"] = new_name
        duplicated_id = transform_name_to_id(new_name)
        duplicated_output["id"] = duplicated_id
        assert res.json() == duplicated_output

        # asserts the matrix has also been duplicated
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw?path=input/st-storage/series/{area_id}/{duplicated_id}/inflows"
        )
        assert res.status_code == 200
        assert res.json()["data"] == array_list

        # =============================
        #  SHORT-TERM STORAGE DELETION
        # =============================

        # To delete a short-term storage, we need to provide its ID.
        res = client.request("DELETE", storage_url, json=[siemens_battery_id])
        assert res.status_code == 204, res.json()
        assert not res.text

        # If the short-term storage list is empty, the deletion should be a no-op.
        res = client.request("DELETE", storage_url, json=[])
        assert res.status_code == 204, res.json()
        assert not res.text

        # It's possible to delete multiple short-term storages at once.
        # In the following example, we will create two short-term storages:
        siemens_properties = {
            "name": siemens_battery,
            "group": "battery",
            "injectionNominalCapacity": 1450,
            "withdrawalNominalCapacity": 1350,
            "reservoirCapacity": 1500,
            "efficiency": 0.90,
            "initialLevel": 0.2,
            "initialLevelOptim": False,
        }
        res = client.post(storage_url, json=siemens_properties)
        assert res.status_code == 200, res.json()
        siemens_battery_id = res.json()["id"]

        # Create another short-term storage: "Grand'Maison"
        grand_maison = "Grand'Maison"
        grand_maison_properties = {
            "name": grand_maison,
            "group": "PSP_Closed",
            "injectionNominalCapacity": 1500,
            "withdrawalNominalCapacity": 1800,
            "reservoirCapacity": 20000,
            "efficiency": 0.78,
            "initialLevel": 1,
        }
        res = client.post(storage_url, json=grand_maison_properties)
        assert res.status_code == 200, res.json()
        grand_maison_id = res.json()["id"]

        # We can check that we have 2 short-term storages in the list.
        # Reading the list of short-term storages
        res = client.get(storage_url)
        assert res.status_code == 200, res.json()
        siemens_output = {**default_output, **siemens_properties, "id": siemens_battery_id}
        grand_maison_output = {**default_output, **grand_maison_properties, "id": grand_maison_id}
        grand_maison_output["group"] = "psp_closed"
        assert res.json() == [duplicated_output, siemens_output, grand_maison_output]

        # We can delete the three short-term storages at once.
        res = client.request(
            "DELETE",
            storage_url,
            json=[grand_maison_id, duplicated_output["id"]],
        )
        assert res.status_code == 204, res.json()
        assert not res.text

        # Only one st-storage should remain.
        res = client.get(storage_url)
        assert res.status_code == 200, res.json()
        assert len(res.json()) == 1

        # ===========================
        #  SHORT-TERM STORAGE ERRORS
        # ===========================

        # Checking only for RAW studies as for variants, we'll always have errors at the generation
        if study_type == "variant":
            return

        # Check delete with the wrong value of `area_id`
        bad_area_id = "bad_area"
        res = client.request(
            "DELETE", f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/storages", json=[siemens_battery_id]
        )
        assert res.status_code == 500
        obj = res.json()

        assert obj["description"] == f"Short-term storage '{siemens_battery_id}' in area '{bad_area_id}' does not exist"
        assert obj["exception"] == "CommandApplicationError"

        # Check delete with the wrong value of `study_id`
        bad_study_id = "bad_study"
        res = client.request(
            "DELETE", f"/v1/studies/{bad_study_id}/areas/{area_id}/storages", json=[siemens_battery_id]
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check get with wrong `area_id`
        res = client.get(f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}")
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check get with wrong `study_id`
        res = client.get(f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}")
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `study_id`
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages", json={"name": siemens_battery, "group": "Battery"}
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check POST with wrong `area_id`
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/storages",
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 500
        obj = res.json()
        assert f"The area '{bad_area_id}' does not exist" in obj["description"]
        assert obj["exception"] == "CommandApplicationError"

        # Check POST with wrong `group`
        res = client.post(
            storage_url,
            json={"name": siemens_battery, "group": "GroupFoo"},
        )
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == f"Free groups are available since v9.2 and your study is in {study_version}"

        # Check PATCH with the wrong `area_id`
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}",
            json={"efficiency": 1.0},
        )
        assert res.status_code == 404
        obj = res.json()
        assert obj["description"] == f"'{bad_area_id}' not a child of InputSTStorageClusters"
        assert obj["exception"] == "ChildNotFoundError"

        # Check PATCH with the wrong `storage_id`
        bad_storage_id = "bad_storage"
        res = client.patch(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/storages/{bad_storage_id}", json={"efficiency": 1.0}
        )
        assert res.status_code == 404
        obj = res.json()
        description = obj["description"]
        assert bad_storage_id in description
        assert re.search(r"'bad_storage'", description, flags=re.IGNORECASE)
        assert re.search(r"not found", description, flags=re.IGNORECASE)

        # Check PATCH with the wrong `study_id`
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}", json={"efficiency": 1.0}
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_study_id in description

        # Cannot duplicate a unknown st-storage
        unknown_id = "unknown"
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas/{area_id}/storages/{unknown_id}", params={"newName": "duplicata"}
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        assert f"'{unknown_id}' not found" in obj["description"]
        assert obj["exception"] == "STStorageNotFound"

        # Cannot duplicate with an existing id
        res = client.post(
            f"{storage_url}/{siemens_battery_id}",
            params={"newName": siemens_battery.upper()},  # different case, but same ID
        )
        assert res.status_code == 409, res.json()
        obj = res.json()
        description = obj["description"]
        assert siemens_battery.lower() in description
        assert obj["exception"] == "DuplicateSTStorage"

        # Cannot specify the field 'enabled' before v8.8
        properties = {"enabled": False, "name": "fake_name", "group": "Battery"}
        res = client.post(storage_url, json=properties)
        if study_version < STUDY_VERSION_8_8:
            assert res.status_code == 422
            assert res.json()["exception"] == "InvalidFieldForVersionError"
        else:
            assert res.status_code == 200
            assert res.json()["enabled"] is False

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    @pytest.mark.parametrize(
        "study_version, default_config, default_output",
        [
            pytest.param(860, ST_STORAGE_INI_860, ST_STORAGE_DICT_860, id="860"),
            pytest.param(880, ST_STORAGE_INI_880, ST_STORAGE_DICT_880, id="880"),
        ],
    )
    def test__default_values(
        self,
        client: TestClient,
        user_access_token: str,
        study_type: str,
        study_version: int,
        default_config: t.Dict[str, t.Any],
        default_output: t.Dict[str, t.Any],
    ) -> None:
        """
        The purpose of this integration test is to test the default values of
        the properties of a short-term storage.

        Given a new study with an area "FR", at least in version 860,
        When I create a short-term storage with a name "Tesla Battery", with the default values,
        Then the short-term storage is created with initialLevel = 0.0, and initialLevelOptim = False.
        """
        # Create a new study in version 860 (or higher)
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.post("/v1/studies", params={"name": "MyStudy", "version": study_version})
        assert res.status_code in {200, 201}, res.json()
        study_id = res.json()

        if study_type == "variant":
            # Create Variant
            res = client.post(f"/v1/studies/{study_id}/variants", params={"name": "Variant 1"})
            assert res.status_code in {200, 201}, res.json()
            study_id = res.json()

        # Create a new area named "FR"
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "FR", "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()
        area_id = res.json()["id"]

        # Create a new short-term storage named "Tesla Battery"
        tesla_battery = "Tesla Battery"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages", json={"name": tesla_battery, "group": "Battery"}
        )
        assert res.status_code == 200, res.json()
        tesla_battery_id = res.json()["id"]
        tesla_output = {**default_output, "id": tesla_battery_id, "name": tesla_battery, "group": "battery"}
        assert res.json() == tesla_output

        # Use the Debug mode to make sure that the initialLevel and initialLevelOptim properties
        # are properly set in the configuration file.
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/st-storage/clusters/{area_id}/list/{tesla_battery_id}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {**default_config, "name": tesla_battery, "group": "battery"}
        assert actual == expected

        # We want to make sure that the default properties are applied to a study variant.
        # We want to make sure that updating the initialLevel property is taken into account
        # in the variant commands.

        # Create a variant of the study
        res = client.post(f"/v1/studies/{study_id}/variants", params={"name": "MyVariant"})
        assert res.status_code in {200, 201}, res.json()
        variant_id = res.json()

        # Create a new short-term storage named "Siemens Battery"
        siemens_battery = "Siemens Battery"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages", json={"name": siemens_battery, "group": "Battery"}
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(f"/v1/studies/{variant_id}/commands")
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 1
        actual = commands[0]
        expected = {
            "id": ANY,
            "action": "create_st_storage",
            "args": {
                "area_id": "fr",
                "parameters": {"name": siemens_battery, "group": "battery"},
                "pmax_injection": ANY,
                "pmax_withdrawal": ANY,
                "lower_rule_curve": ANY,
                "upper_rule_curve": ANY,
                "inflows": ANY,
            },
            "version": 3,
            "updated_at": ANY,
            "user_name": ANY,
        }
        assert actual == expected

        # Update the initialLevel property of the "Siemens Battery" short-term storage to 0.5
        siemens_battery_id = transform_name_to_id(siemens_battery)
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{siemens_battery_id}", json={"initialLevel": 0.5}
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(f"/v1/studies/{variant_id}/commands")
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 2
        actual = commands[1]
        expected = {
            "id": ANY,
            "action": "update_st_storages",
            "args": {"storage_properties": {"fr": {"siemens battery": {"initial_level": 0.5}}}},
            "version": 1,
            "updated_at": ANY,
            "user_name": ANY,
        }
        assert actual == expected

        # Update the initialLevel property of the "Siemens Battery" short-term storage back to 0
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{siemens_battery_id}",
            json={"initialLevel": 0.0, "injectionNominalCapacity": 1600},
        )
        assert res.status_code == 200, res.json()

        # Check the variant commands
        res = client.get(f"/v1/studies/{variant_id}/commands")
        assert res.status_code == 200, res.json()
        commands = res.json()
        assert len(commands) == 3
        actual = commands[2]
        expected = {
            "id": ANY,
            "action": "update_st_storages",
            "args": {
                "storage_properties": {
                    "fr": {"siemens battery": {"initial_level": 0.0, "injection_nominal_capacity": 1600.0}}
                }
            },
            "version": 1,
            "updated_at": ANY,
            "user_name": ANY,
        }
        assert actual == expected

        # Use the Debug mode to make sure that the initialLevel and initialLevelOptim properties
        # are properly set in the configuration file.
        res = client.get(
            f"/v1/studies/{variant_id}/raw",
            params={"path": f"input/st-storage/clusters/{area_id}/list/{siemens_battery_id}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected = {
            **default_config,
            "name": siemens_battery,
            "group": "battery",
            "injectionnominalcapacity": 1600,
            "initiallevel": 0.0,
        }
        assert actual == expected

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
        In this test, we want to check that short-term storages can be managed
        in the context of a "variant" study.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Create an area
        area_name = "France"
        res = client.post(f"/v1/studies/{variant_id}/areas", json={"name": area_name, "type": "AREA"})
        assert res.status_code in {200, 201}, res.json()
        area_cfg = res.json()
        area_id = area_cfg["id"]

        # Create a short-term storage
        cluster_name = "Tesla1"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages",
            json={
                "name": cluster_name,
                "group": "Battery",
                "injectionNominalCapacity": 4500,
                "withdrawalNominalCapacity": 4230,
                "reservoirCapacity": 5700,
            },
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_id: str = res.json()["id"]

        # Update the short-term storage
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{cluster_id}", json={"reservoirCapacity": 5600}
        )
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["reservoirCapacity"] == 5600

        # Update the series matrix
        matrix = np.random.randint(0, 2, size=(8760, 1)).tolist()
        matrix_path = f"input/st-storage/series/{area_id}/{cluster_id.lower()}/pmax_injection"
        args = {"target": matrix_path, "matrix": matrix}
        res = client.post(f"/v1/studies/{variant_id}/commands", json=[{"action": "replace_matrix", "args": args}])
        assert res.status_code in {200, 201}, res.json()

        # Duplicate the short-term storage
        new_name = "Tesla2"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/{cluster_id}", params={"newName": new_name}
        )
        assert res.status_code in {200, 201}, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["name"] == new_name
        new_id = cluster_cfg["id"]

        # Check that the duplicate has the right properties
        res = client.get(f"/v1/studies/{variant_id}/areas/{area_id}/storages/{new_id}")
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["group"] == "battery"
        assert cluster_cfg["injectionNominalCapacity"] == 4500
        assert cluster_cfg["withdrawalNominalCapacity"] == 4230
        assert cluster_cfg["reservoirCapacity"] == 5600

        # Check that the duplicate has the right matrix
        new_cluster_matrix_path = f"input/st-storage/series/{area_id}/{new_id.lower()}/pmax_injection"
        res = client.get(f"/v1/studies/{variant_id}/raw", params={"path": new_cluster_matrix_path})
        assert res.status_code == 200
        assert res.json()["data"] == matrix

        # Delete the short-term storage
        # usage of request instead of delete as httpx doesn't support delete with a payload anymore.
        res = client.request(
            method="DELETE", url=f"/v1/studies/{variant_id}/areas/{area_id}/storages", json=[cluster_id]
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
            "create_st_storage",
            "update_st_storages",
            "replace_matrix",
            "create_st_storage",
            "replace_matrix",
            "remove_st_storage",
        ]

    @pytest.mark.parametrize("base_study_id", [{"name": "Base Study", "version": 860}], indirect=True)
    @pytest.mark.parametrize("variant_id", ["Variant Study"], indirect=True)
    def test_uppercase_name_update(self, client: TestClient, user_access_token: str, variant_id: str) -> None:
        """
        In this test, we want to check that short-term storages are updated correctly
        also when the identifier in the section name is in uppercase, which
        happens when studies are created outside from antares-web.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create an area
        area_name = "France"
        res = client.post(f"/v1/studies/{variant_id}/areas", json={"name": area_name, "type": "AREA"})
        assert res.status_code == 200, res.json()
        area_cfg = res.json()
        area_id = area_cfg["id"]

        # Create a short-term storage
        cluster_name = "Tesla1"
        res = client.post(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages",
            json={
                "name": cluster_name,
                "group": "Battery",
                "injectionNominalCapacity": 4500,
                "withdrawalNominalCapacity": 4230,
                "reservoirCapacity": 5700,
            },
        )
        assert res.status_code == 200, res.json()
        assert res.json()["id"] == "tesla1"

        # Perform raw call in order to change the section name to upper case "Tesla1"
        res = client.get(f"/v1/studies/{variant_id}/raw?path=input/st-storage/clusters/{area_id}/list")
        assert res.status_code == 200, res.json()
        content = dict(res.json())
        assert list(content.keys()) == ["tesla1"]
        content["Tesla1"] = content.pop("tesla1")
        res = client.post(f"/v1/studies/{variant_id}/raw?path=input/st-storage/clusters/{area_id}/list", json=content)
        assert res.status_code == 200, res.json()
        res = client.get(f"/v1/studies/{variant_id}/raw?path=input/st-storage/clusters/{area_id}/list")
        assert res.status_code == 200, res.json()
        assert list(res.json().keys()) == ["Tesla1"]

        # Now INI section has capitals, we update the short-term storage using its ID
        res = client.patch(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages/tesla1", json={"reservoirCapacity": 5600}
        )
        assert res.status_code == 200, res.json()
        cluster_cfg = res.json()
        assert cluster_cfg["reservoirCapacity"] == 5600

        # Check that getting the list works and that is has correctly been updated
        res = client.get(
            f"/v1/studies/{variant_id}/areas/{area_id}/storages",
        )
        assert res.status_code in {200, 201}, res.json()
        assert res.json()[0]["reservoirCapacity"] == 5600
