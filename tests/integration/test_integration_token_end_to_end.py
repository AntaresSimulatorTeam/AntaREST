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

import io
import typing as t
from unittest.mock import ANY

import numpy as np
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.launcher.model import JobResultDTO, JobStatus
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_for


class CommandDict(t.TypedDict):
    action: str
    args: t.Dict[str, t.Any]


def test_nominal_case_of_an_api_user(client: TestClient, admin_access_token: str) -> None:
    """
    Test the nominal case for an API user, which includes creating a **bot**, importing a study,
    creating a variant, editing study configurations, creating thermal clusters, generating a variant,
    running a simulation, and performing various other operations.
    The test checks the success and status codes of the API endpoints.
    """
    study_path = ASSETS_DIR / "STA-mini.zip"

    # create a bot
    res = client.post(
        "/v1/bots",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={"name": "admin_bot", "roles": [{"group": "admin", "role": 40}], "is_author": False},
    )
    bot_headers = {"Authorization": f"Bearer {res.json()}"}

    # import a study
    res = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(study_path.read_bytes())},
        headers=bot_headers,
    )
    study_id = res.json()

    # create a variant from it
    res = client.post(f"/v1/studies/{study_id}/variants", headers=bot_headers, params={"name": "foo"})
    variant_id = res.json()

    # get the first area id of the study
    res = client.get(f"/v1/studies/{variant_id}/areas", headers=bot_headers)
    area_id = res.json()[0]["id"]

    # edit an area (for instance its geographic trimming attribute)
    res = client.put(
        f"/v1/studies/{variant_id}/config/general/form",
        headers=bot_headers,
        json={"yearByYear": True},
    )
    assert res.status_code == 200
    commands: t.List[CommandDict]
    commands = [
        {
            "action": "update_config",
            "args": {
                "target": f"input/areas/{area_id}/optimization/filtering/filter_synthesis",
                "data": "annual",
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=commands)
    assert res.status_code == 200

    # modify its playlist (to do so, set its mcYears to more than the biggest year of the playlist)
    res = client.put(f"/v1/studies/{variant_id}/config/general/form", headers=bot_headers, json={"nbYears": 10})
    assert res.status_code == 200
    res = client.put(f"/v1/studies/{variant_id}/config/playlist", headers=bot_headers, json={"playlist": [1, 4, 7]})
    assert res.status_code == 200

    # create a first simple thermal cluster
    commands = [
        {
            "action": "create_cluster",
            "args": {
                "area_id": area_id,
                "cluster_name": "mycluster",
                "parameters": {
                    "group": "Gas",
                    "unitcount": 1,
                    "marginal_cost": 50,
                },
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=commands)
    assert res.status_code == 200

    # create a second thermal cluster with a lot of arguments
    cluster_id = "new_cluster"
    commands = [
        {
            "action": "create_cluster",
            "args": {
                "area_id": area_id,
                "cluster_name": cluster_id,
                "parameters": {
                    "group": "Gas",
                    "marginal-cost": 98,
                    "unitcount": 1,
                    "nominalcapacity": 250,
                    "min-stable-power": 0.0,
                    "min-up-time": 2,
                    "min-down-time": 2,
                    "spinning": 5,
                    "spread-cost": 0.0,
                    "startup-cost": 2500,
                    "market-bid-cost": 85,
                    "co2": 0.3,
                },
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=commands)
    assert res.status_code == 200
    # add time_series matrix
    command_matrix = [
        {
            "action": "replace_matrix",
            "args": {
                "target": f"input/thermal/series/{area_id}/{cluster_id}/series",
                "matrix": np.zeros((8760, 3), dtype=np.float64).tolist(),
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command_matrix)
    assert res.status_code == 200
    # add prepro data matrix
    command_matrix[0]["args"]["target"] = f"input/thermal/prepro/{area_id}/{cluster_id}/data"
    data_matrix = np.zeros((365, 6), dtype=np.float64)
    data_matrix[:, 2:6] = 1
    command_matrix[0]["args"]["matrix"] = data_matrix.tolist()
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command_matrix)
    assert res.status_code == 200
    # add prepro modulation matrix
    command_matrix[0]["args"]["target"] = f"input/thermal/prepro/{area_id}/{cluster_id}/modulation"
    modulation_matrix = np.ones((8760, 4), dtype=np.float64)
    modulation_matrix[:, 3] = 0
    command_matrix[0]["args"]["matrix"] = modulation_matrix.tolist()
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command_matrix)
    assert res.status_code == 200

    # edit existing cluster with only one argument
    # noinspection SpellCheckingInspection
    commands = [
        {
            "action": "update_config",
            "args": {
                "target": f"input/thermal/clusters/{area_id}/list/{cluster_id}/nominalcapacity",
                "data": 300,
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=commands)
    assert res.status_code == 200

    # Check if the author's name and date of update are retrieved with commands created by a bot
    commands_res = client.get(f"/v1/studies/{variant_id}/commands", headers=bot_headers)

    for command in commands_res.json():
        assert command["user_name"] == "admin_bot"
        assert command["updated_at"]

    # generate variant before running a simulation
    res = client.put(f"/v1/studies/{variant_id}/generate", headers=bot_headers)
    assert res.status_code == 200
    res = client.get(
        f"/v1/tasks/{res.json()}",
        headers=bot_headers,
        params={"wait_for_completion": True},
    )
    assert res.status_code == 200
    task_result = TaskDTO(**res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result is not None
    assert task_result.result.success

    # run the simulation
    launcher_options = {"nb_cpu": 18, "auto_unzip": True, "output_suffix": "launched_by_bot"}
    res = client.post(f"/v1/launcher/run/{variant_id}", json=launcher_options, headers=bot_headers)
    job_id = res.json()["job_id"]

    # note: this list is used to collect job result for debugging purposes
    job_results: t.List[JobResultDTO] = []

    def wait_unit_finished() -> bool:
        res_ = client.get(f"/v1/launcher/jobs/{job_id}", headers=bot_headers)
        job_result_ = JobResultDTO(**res_.json())
        job_results.append(job_result_)
        return job_result_.status in {JobStatus.SUCCESS, JobStatus.FAILED}

    wait_for(wait_unit_finished)

    # The launching is simulated, and no output is generated, so we expect to have a failure
    # since the job will not be able to get the outputs.
    assert job_results[-1].status == JobStatus.FAILED

    # read a result
    res = client.get(f"/v1/studies/{study_id}/outputs", headers=bot_headers)
    assert len(res.json()) == 6
    first_output_name = res.json()[0]["name"]
    res = client.get(
        f"/v1/studies/{study_id}/raw",
        headers=bot_headers,
        params={
            "path": f"output/{first_output_name}/economy/mc-all/areas/{area_id}/details-monthly",
            "depth": 3,
        },
    )
    assert res.json() == {"index": ANY, "columns": ANY, "data": ANY}

    # remove output
    client.delete(f"/v1/studies/{study_id}/outputs/{first_output_name}", headers=bot_headers)
    res = client.get(f"/v1/studies/{study_id}/outputs", headers=bot_headers)
    assert len(res.json()) == 5

    # delete variant
    res = client.delete(f"/v1/studies/{variant_id}", headers=bot_headers)
    assert res.status_code == 200
