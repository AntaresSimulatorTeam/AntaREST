import io
import time
from http import HTTPStatus
from pathlib import Path
from unittest.mock import ANY

import numpy as np
from starlette.testclient import TestClient

from antarest.core.model import PublicMode
from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.study.business.adequacy_patch_management import PriceTakingOrder
from antarest.study.business.area_management import AreaType, LayerInfoDTO
from antarest.study.business.areas.properties_management import AdequacyPatchMode
from antarest.study.business.areas.renewable_management import TimeSeriesInterpretation
from antarest.study.business.areas.thermal_management import LawOption, TimeSeriesGenerationOption
from antarest.study.business.general_management import Mode
from antarest.study.business.optimization_management import (
    SimplexOptimizationRange,
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
)
from antarest.study.business.table_mode_management import (
    FIELDS_INFO_BY_TYPE,
    AssetType,
    BindingConstraintOperator,
    BindingConstraintType,
    TableTemplateType,
    TransmissionCapacity,
)
from antarest.study.model import MatrixIndex, StudyDownloadLevelDTO
from antarest.study.storage.variantstudy.model.command.common import CommandName
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_for


def test_copy(client: TestClient, admin_access_token: str, study_id: str) -> None:
    study_path = ASSETS_DIR / "STA-mini.zip"

    # todo : ajouter des tests partout :/

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

    # edit an area (for instance its geographic trimming attribute)
    """
    geo_trim = getGeographicTrimming(areas=area_name, opts=var_opts)
	area_filter = geo_trim$areas[["fr"]]
	area_filter$`filter-synthesis` = "annual"
	editArea("fr", filtering = area_filter, opts=var_opts)
    """

    # modify its playlist (to do so, set its mcYears to more than the biggest year of the playlist)
    res = client.put(f"/v1/studies/{variant_id}/config/general/form", headers=bot_headers, json={"nbYears": 10})
    res = client.put(f"/v1/studies/{variant_id}/config/playlist", headers=bot_headers, json={"playlist": [1, 4, 7]})

    # get the first area id of the study
    res = client.get(f"/v1/studies/{variant_id}/areas", headers=bot_headers)
    area_id = res.json()[0]["id"]

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
    # add prepro data matrix
    command_matrix[0]["args"]["target"] = f"input/thermal/prepro/{area_id}/{cluster_id}/data"
    data_matrix = np.zeros((365, 6), dtype=np.float64)
    data_matrix[:, 2:6] = 1
    command_matrix[0]["args"]["matrix"] = data_matrix.tolist()
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command_matrix)
    # add prepro modulation matrix
    command_matrix[0]["args"]["target"] = f"input/thermal/prepro/{area_id}/{cluster_id}/modulation"
    modulation_matrix = np.ones((8760, 4), dtype=np.float64)
    modulation_matrix[:, 3] = 0
    command_matrix[0]["args"]["matrix"] = modulation_matrix.tolist()
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command_matrix)

    # edit existing cluster with only one argument
    command = [
        {
            "action": "update_config",
            "args": {"target": f"input/thermal/clusters/{area_id}/list/{cluster_id}/nominalcapacity", "data": 300},
        }
    ]
    res = client.post(f"/v1/studies/{variant_id}/commands", headers=bot_headers, json=command)

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
    job_id = res.json()['job_id']
    res = client.get(f"/v1/launcher/jobs/{job_id}", headers=bot_headers)
    i = 10
    while i > 0 or res.json()["status"] not in ['failed', 'success']:
        res = client.get(f"/v1/launcher/jobs/{job_id}", headers=bot_headers)
        time.sleep(0.5)
        i -= 1
    print(res.json()["status"])

    # gather the results and see use of cluster in mc-all ?

    # remove output

    # gather tasks (do not know when use it)

