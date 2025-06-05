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
from unittest.mock import ANY

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from tests.integration.utils import wait_task_completion


@pytest.mark.integration_test
class TestSTStorage:
    """
    This unit test is designed to demonstrate the creation, modification of properties and
    updating of matrices, and the deletion of one or more short-term storages.
    """

    # noinspection SpellCheckingInspection
    def test_lifecycle(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        # =======================
        #  Study version upgrade
        # =======================

        # We have an "old" study that we need to upgrade to version 860
        min_study_version = 860
        res = client.put(
            f"/v1/studies/{internal_study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": min_study_version},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # We can check that the study is upgraded to the required version
        res = client.get(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert res.json() == {
            "id": internal_study_id,
            "name": "STA-mini",
            "version": min_study_version,
            "created": ANY,  # ISO8601 Date/time
            "updated": ANY,  # ISO8601 Date/time
            "type": "rawstudy",
            "owner": {"id": None, "name": ANY},
            "groups": [],
            "public_mode": "FULL",
            "workspace": "ext",
            "managed": False,
            "archived": False,
            "horizon": "2030",
            "folder": "STA-mini",
            "tags": [],
        }

        # Here is the list of available areas
        res = client.get(
            f"/v1/studies/{internal_study_id}/areas",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        areas = res.json()
        area_ids = {a["id"] for a in areas if a["type"] == "AREA"}
        assert area_ids == {"es", "it", "de", "fr"}

        # =============================================
        #  Short-Term Storage Creation w/o Time Series
        # =============================================

        # First, we will define a short-term storage in the geographical
        # area "FR" called "Siemens Battery" with the bellow arguments.
        # We will use the default values for the time series:
        # - `pmax_injection`: Charge capacity,
        # - `pmax_withdrawal`: Discharge capacity,
        # - `lower_rule_curve`: Lower rule curve,
        # - `upper_rule_curve`: Upper rule curve,
        # - `inflows`: Inflows
        area_id = transform_name_to_id("FR")
        siemens_battery = "Siemens Battery"
        args = {
            "area_id": area_id,
            "parameters": {
                "name": siemens_battery,
                "group": "Battery",
                "injection_nominal_capacity": 150,
                "withdrawal_nominal_capacity": 150,
                "reservoir_capacity": 600,
                "efficiency": 0.94,
                "initial_level_optim": True,
            },
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_st_storage", "version": 2, "args": args}],
        )
        res.raise_for_status()

        # =======================================
        #  Short-Term Storage Time Series Update
        # =======================================

        # Then, it is possible to update a time series.
        # For instance, we want to initialize the `inflows` time series
        # with random values (for this demo).
        # To do that, we can use the `replace_matrix` command like bellow:
        siemens_battery_id = transform_name_to_id(siemens_battery)
        inflows = np.random.randint(0, 1001, size=(8760, 1))
        args1 = {
            "target": f"input/st-storage/series/{area_id}/{siemens_battery_id}/inflows",
            "matrix": inflows.tolist(),
        }
        pmax_injection = np.random.rand(8760, 1)
        args2 = {
            "target": f"input/st-storage/series/{area_id}/{siemens_battery_id}/pmax_injection",
            "matrix": pmax_injection.tolist(),
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {"action": "replace_matrix", "args": args1},
                {"action": "replace_matrix", "args": args2},
            ],
        )
        res.raise_for_status()

        # ==============================================
        #  Short-Term Storage Creation with Time Series
        # ==============================================

        # Another way to create a Short-Term Storage is by providing
        # both the parameters and the time series arrays.
        # Here is an example where we populate some arrays with random values.
        pmax_injection = np.random.rand(8760, 1)
        pmax_withdrawal = np.random.rand(8760, 1)
        inflows = np.random.randint(0, 1001, size=(8760, 1))
        grand_maison = "Grand'Maison"
        args = {
            "area_id": area_id,
            "parameters": {
                "name": grand_maison,
                "group": "PSP_closed",
                "injectionnominalcapacity": 1500,
                "withdrawalnominalcapacity": 1800,
                "reservoircapacity": 20000,
                "efficiency": 0.78,
                "initiallevel": 0.91,
            },
            "pmax_injection": pmax_injection.tolist(),
            "pmax_withdrawal": pmax_withdrawal.tolist(),
            "inflows": inflows.tolist(),
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_st_storage", "version": 2, "args": args}],
        )
        res.raise_for_status()

        # ============================
        #  Short-Term Storage Removal
        # ============================

        # The `remove_st_storage` command allows you to delete a Short-Term Storage.
        args = {"area_id": area_id, "storage_id": siemens_battery_id}
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "remove_st_storage", "args": args}],
        )
        res.raise_for_status()

        # =======================================
        #  Parameters and Time Series Validation
        # =======================================

        # When creating a Short-Term Storage, both the validity of the parameters
        # (value type and valid range) and the validity of the time series
        # (value range) are checked.
        # In the example below, multiple parameters are invalid, and one matrix contains
        # values outside the valid range. Upon executing the request, an HTTP 422
        # error occurs, and a response specifies the invalid values.
        pmax_injection = np.random.rand(8760, 1)
        pmax_withdrawal = np.random.rand(8760, 1) * 10  # Oops!
        inflows = np.random.randint(0, 1001, size=(8760, 1))
        args = {
            "area_id": area_id,
            "parameters": {
                "name": "Bad Storage",
                "group": "Wonderland",  # Oops!
                "injection_nominal_capacity": 2000,
                "withdrawal_nominal_capacity": 1500,
                "reservoir_capacity": 20000,
                "efficiency": 0.78,
                "initial_level": 0.91,
                "initial_level_optim": False,
            },
            "pmax_injection": pmax_injection.tolist(),
            "pmax_withdrawal": pmax_withdrawal.tolist(),
            "inflows": inflows.tolist(),
        }
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_st_storage", "args": args}],
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY
        description = res.json()["description"]
        assert "Free groups are available since v9.2 and your study is in 8.6" in description

        args["parameters"]["group"] = "psp_open"
        res = client.post(
            f"/v1/studies/{internal_study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_st_storage", "args": args}],
        )
        assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY
        description = res.json()["description"]
        assert "Matrix values should be between 0 and 1" in description
