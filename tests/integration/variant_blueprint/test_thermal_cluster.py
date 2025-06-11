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
import random
import typing as t
from unittest import mock

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


def _create_thermal_params(cluster_name: str) -> t.Mapping[str, t.Any]:
    # noinspection SpellCheckingInspection
    return {
        "name": cluster_name,
        "group": "Gas",
        "unitcount": random.randint(1, 10),
        "nominalcapacity": random.random() * 1000,
        "min-stable-power": random.random() * 1000,
        "min-up-time": random.randint(1, 168),
        "min-down-time": random.randint(1, 168),
        "co2": random.random() * 10,
        "marginal-cost": random.random() * 100,
        "spread-cost": random.random(),
        "startup-cost": random.random() * 100000,
        "market-bid-cost": random.random() * 100,
    }


@pytest.mark.integration_test
class TestThermalCluster:
    """
    The goal of this test is to check the performance of the update
    of the properties and matrices of the thermal clusters in the case where we
    have a cascade of study variants.
    We want also to check that the variant snapshots are correctly created without
    blocking thread (no timeout).
    """

    def test_cascade_update(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test is based on the study "STA-mini.zip", which is a RAW study.
        We will first convert this study to a managed study, and then we will
        create a cascade of _N_ variants (more than `max_workers`).
        Finally, we will read the thermal clusters of all areas of the last variant
        to check that the variant generation is not blocking.
        """
        # First, we create a copy of the study, and we convert it to a managed study.
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"study_name": "default", "with_outputs": False, "use_task": False},
        )
        assert res.status_code == http.HTTPStatus.CREATED, res.json()
        base_study_id = res.json()
        assert base_study_id is not None

        # Store the variant IDs in a list.
        cascade_ids = [base_study_id]
        total_count = 6  # `max_workers` is set to 5 in the configuration (default value).
        for count in range(1, total_count + 1):
            # Create a new variant of the last study in the cascade.
            prev_id = cascade_ids[-1]
            res = client.post(
                f"/v1/studies/{prev_id}/variants",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"name": f"Variant {count}"},
            )
            assert res.status_code == http.HTTPStatus.OK, res.json()  # should be CREATED
            variant_id = res.json()
            assert variant_id is not None
            cascade_ids.append(variant_id)

            # Create a thermal cluster in an area (randomly chosen).
            area_id = "fr"
            cluster_name = f"Cluster {count}"
            cmd_args = {
                "action": "create_cluster",
                "args": {
                    "area_id": area_id,
                    "cluster_name": transform_name_to_id(cluster_name, lower=False),
                    "parameters": _create_thermal_params(cluster_name),
                    "prepro": np.random.rand(8760, 6).tolist(),
                    "modulation": np.random.rand(8760, 4).tolist(),
                },
            }
            res = client.post(
                f"/v1/studies/{variant_id}/commands",
                headers={"Authorization": f"Bearer {user_access_token}"},
                json=[cmd_args],
            )
            assert res.status_code == http.HTTPStatus.OK, res.json()  # should be CREATED

        # At this point, we have a base study copied in the default workspace,
        # and a certain number of variants stored in the database.
        # But no variant is physically stored in the default workspace.
        res = client.get(
            "/v1/studies",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"managed": True},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        study_map = res.json()  # dict of study properties, indexed by study ID
        assert set(study_map) | {base_study_id} == set(cascade_ids)

        # Now, we will generate the last variant
        variant_id = cascade_ids[-1]
        res = client.put(
            f"/v1/studies/{variant_id}/generate",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"denormalize": False, "from_scratch": True},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        task_id = res.json()

        # wait for task completion
        res = client.get(
            f"/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"wait_for_completion": True, "timeout": 10},
        )
        assert res.status_code == http.HTTPStatus.OK, res.json()
        task = TaskDTO(**res.json())
        assert task.model_dump() == {
            "completion_date_utc": mock.ANY,
            "creation_date_utc": mock.ANY,
            "id": task_id,
            "logs": None,
            "name": f"Generation of {variant_id} study",
            "owner": 2,
            "ref_id": variant_id,
            "result": {
                "message": f"{variant_id} generated successfully",
                "return_value": mock.ANY,
                "success": True,
            },
            "status": TaskStatus.COMPLETED,
            "type": "VARIANT_GENERATION",
            "progress": None,
        }
