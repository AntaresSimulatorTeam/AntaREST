import io
from unittest.mock import ANY

import numpy as np
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from tests.integration.assets import ASSETS_DIR


def test_nominal_case_of_an_api_user(client: TestClient, admin_access_token: str, study_id: str) -> None:
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
    uuid = res.json()

    # create a variant from it
    res = client.post(f"/v1/studies/{uuid}/variants?name=foo", headers=bot_headers)
    variant_id = res.json()

    # get the first area id of the study
    res = client.get(f"/v1/studies/{variant_id}/areas", headers=bot_headers)
    area_id = res.json()[0]["id"]

    # edit an area (for instance its geographic trimming attribute)
    res = client.put(
        f"/v1/studies/{variant_id}/config/general/form", headers=bot_headers, json={"geographicTrimming": True}
    )
    assert res.status_code == 200
    command = [
        {
            "action": "update_config",
            "args": {
                "target": f"input/areas/{area_id}/optimization/filtering/filter_synthesis",
                "data": "annual",
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command)
    assert res.status_code == 200

    # modify its playlist (to do so, set its mcYears to more than the biggest year of the playlist)
    res = client.put(f"/v1/studies/{variant_id}/config/general/form", headers=bot_headers, json={"nbYears": 10})
    assert res.status_code == 200
    res = client.put(f"/v1/studies/{variant_id}/config/playlist", headers=bot_headers, json={"playlist": [1, 4, 7]})
    assert res.status_code == 200

    # create a first simple thermal cluster
    command = [
        {
            "action": "create_cluster",
            "args": {
                "area_id": area_id,
                "cluster_name": "mycluster",
                "parameters": {
                    "group": "Gas",
                    "unitCount": 1,
                    "marginal_cost": 50,
                },
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command)
    assert res.status_code == 200

    # create a second thermal cluster with a lot of arguments
    cluster_id = "newcluster"
    command = [
        {
            "action": "create_cluster",
            "args": {
                "area_id": area_id,
                "cluster_name": cluster_id,
                "parameters": {
                    "group": "Gas",
                    "marginal-cost": 98,
                    "unitCount": 1,
                    "nominalCapacity": 250,
                    "minStablePower": 0.0,
                    "minUpTime": 2,
                    "minDownTime": 2,
                    "spinning": 5,
                    "spreadCost": 0.0,
                    "startupCost": 2500,
                    "marketBidCost": 85,
                    "co2": 0.3,
                },
            },
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command)
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
    command = [
        {
            "action": "update_config",
            "args": {"target": f"input/thermal/clusters/{area_id}/list/{cluster_id}/nominalcapacity", "data": 300},
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command)
    assert res.status_code == 200

    # generate variant before running a simulation
    res = client.put(f"/v1/studies/{variant_id}/generate", headers=bot_headers)
    assert res.status_code == 200
    res = client.get(f"/v1/tasks/{res.json()}?wait_for_completion=true", headers=bot_headers)
    assert res.status_code == 200
    task_result = TaskDTO.parse_obj(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result.success

    # run the simulation
    launcher_options = {"nb_cpu": 18, "auto_unzip": True, "output_suffix": "launched_by_bot"}
    res = client.post(f"/v1/launcher/run/{variant_id}", json=launcher_options, headers=bot_headers)
    res = client.get(f"/v1/launcher/jobs/{res.json()['job_id']}", headers=bot_headers)
    assert res.json()["status"] in ["pending", "running"]

    # read a result
    res = client.get(f"/v1/studies/{study_id}/outputs", headers=bot_headers)
    assert len(res.json()) == 5
    first_output_name = res.json()[0]["name"]
    res = client.get(
        f"/v1/studies/{study_id}/raw?path=output/{first_output_name}/economy/mc-all/areas/{area_id}/details-monthly&depth=3",
        headers=bot_headers,
    )
    assert res.json() == {"index": ANY, "columns": ANY, "data": ANY}

    # remove output
    client.delete(f"/v1/studies/{study_id}/outputs/{first_output_name}", headers=bot_headers)
    res = client.get(f"/v1/studies/{study_id}/outputs", headers=bot_headers)
    assert len(res.json()) == 4

    # delete variant
    res = client.delete(f"/v1/studies/{variant_id}", headers=bot_headers)
    assert res.status_code == 200
