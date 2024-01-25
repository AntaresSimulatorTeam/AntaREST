import datetime
import io
import os
from http import HTTPStatus
from pathlib import Path
from unittest.mock import ANY

import numpy as np
import pandas as pd
from starlette.testclient import TestClient

from antarest.core.model import PublicMode
from antarest.launcher.model import LauncherLoadDTO
from antarest.study.business.adequacy_patch_management import PriceTakingOrder
from antarest.study.business.area_management import AreaType, LayerInfoDTO
from antarest.study.business.areas.properties_management import AdequacyPatchMode
from antarest.study.business.areas.renewable_management import TimeSeriesInterpretation
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
    TableTemplateType,
    TransmissionCapacity,
)
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableClusterGroup
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import LawOption, LocalTSGenerationBehavior
from antarest.study.storage.variantstudy.model.command.common import CommandName
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_for


def test_main(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # create some new users
    # TODO check for bad username or empty password
    client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "George", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "Fred", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "Harry", "password": "mypass"},
    )
    res = client.get("/v1/users", headers=admin_headers)
    assert len(res.json()) == 4

    # reject user with existing name creation
    res = client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "George", "password": "mypass"},
    )
    assert res.status_code == 400

    # login with new user
    # TODO mock ldap connector and test user login
    res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
    res.raise_for_status()
    george_credentials = res.json()

    res = client.post("/v1/login", json={"username": "Fred", "password": "mypass"})
    res.raise_for_status()
    fred_credentials = res.json()
    fred_id = fred_credentials["user"]

    res = client.post("/v1/login", json={"username": "Harry", "password": "mypass"})
    res.raise_for_status()

    # reject user creation from non admin
    res = client.post(
        "/v1/users",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json={"name": "Fred", "password": "mypass"},
    )
    assert res.status_code == 403

    # check study listing
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 1
    study_id = next(iter(res.json()))

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    res_output = res.json()
    assert len(res_output) == 5

    res = client.get(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco/variables",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 417
    assert res.json()["description"] == "Not a year by year simulation"

    # study synthesis
    res = client.get(
        f"/v1/studies/{study_id}/synthesis",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200, res.json()

    # playlist
    res = client.post(
        f"/v1/studies/{study_id}/raw?path=settings/generaldata/general/nbyears",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json=5,
    )
    assert res.status_code == 204

    res = client.put(
        f"/v1/studies/{study_id}/config/playlist",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json={"playlist": [1, 2], "weights": {1: 8.0, 3: 9.0}},
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/config/playlist",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200
    assert res.json() == {"1": 8.0, "2": 1.0}

    # scenario builder
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json={
            "ruleset test": {
                "l": {"area1": {"0": 1}},
                "ntc": {"area1 / area2": {"1": 23}},
                "t": {"area1": {"thermal": {"1": 2}}},
            },
            "Default Ruleset": "",
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200
    assert res.json() == {
        "ruleset test": {
            "l": {"area1": {"0": 1}},
            "ntc": {"area1 / area2": {"1": 23}},
            "t": {"area1": {"thermal": {"1": 2}}},
        },
    }

    # config / thematic trimming
    res = client.get(
        f"/v1/studies/{study_id}/config/thematictrimming/form",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200

    res = client.delete(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 4

    # study creation
    created = client.post(
        "/v1/studies?name=foo",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert created.status_code == 201

    res = client.get(
        f"/v1/studies/{created.json()}/raw?path=study&depth=3&formatted=true",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.json()["antares"]["author"] == "George"

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 2

    # Study copy
    copied = client.post(
        f"/v1/studies/{created.json()}/copy?dest=copied&use_task=false",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert copied.status_code == 201

    updated = client.put(
        f"/v1/studies/{copied.json()}/move?folder_dest=foo/bar",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert updated.status_code == 200

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 3
    assert filter(lambda s: s["id"] == copied.json(), res.json().values()).__next__()["folder"] == "foo/bar"

    # Study delete
    client.delete(
        f"/v1/studies/{copied.json()}",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 2

    # check study permission
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
    )
    assert len(res.json()) == 1

    # play with groups
    client.post(
        "/v1/groups",
        headers=admin_headers,
        json={"name": "Weasley"},
    )
    res = client.get("/v1/groups", headers=admin_headers)
    group_id = res.json()[1]["id"]
    client.post(
        "/v1/roles",
        headers=admin_headers,
        json={"type": 40, "group_id": group_id, "identity_id": 3},
    )
    client.post(
        "/v1/roles",
        headers=admin_headers,
        json={"type": 30, "group_id": group_id, "identity_id": 2},
    )
    # reset login to update credentials
    res = client.post(
        "/v1/refresh",
        headers={"Authorization": f'Bearer {george_credentials["refresh_token"]}'},
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/refresh",
        headers={"Authorization": f'Bearer {fred_credentials["refresh_token"]}'},
    )
    fred_credentials = res.json()
    res = client.post(
        f"/v1/studies?name=bar&groups={group_id}",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 3
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
    )
    assert len(res.json()) == 2

    # running studies
    # TODO use a local launcher mock instead of using a local launcher with launcher_mock.sh (doesn't work..)
    studies = [study_id for study_id in res.json() if res.json()[study_id]["name"] == "STA-mini"]
    study_id = studies[0]
    res = client.post(
        f"/v1/launcher/run/{study_id}",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
    )
    job_id = res.json()["job_id"]

    res = client.get("/v1/launcher/load", headers=admin_headers)
    assert res.status_code == 200, res.json()
    launcher_load = LauncherLoadDTO.parse_obj(res.json())
    assert launcher_load.allocated_cpu_rate == 1 / (os.cpu_count() or 1)
    assert launcher_load.cluster_load_rate == 1 / (os.cpu_count() or 1)
    assert launcher_load.nb_queued_jobs == 0
    assert launcher_load.launcher_status == "SUCCESS"

    res = client.get(
        f"/v1/launcher/jobs?study_id={study_id}",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
    )
    job_info = res.json()[0]
    assert job_info == {
        "id": job_id,
        "study_id": study_id,
        "launcher": "local",
        "launcher_params": ANY,
        "status": "pending",
        "creation_date": ANY,
        "completion_date": None,
        "msg": None,
        "output_id": None,
        "exit_code": None,
        "solver_stats": None,
        "owner": {"id": fred_id, "name": "Fred"},
    }

    # update metadata
    res = client.put(
        f"/v1/studies/{study_id}",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
        json={
            "name": "STA-mini-copy",
            "status": "copied",
            "horizon": "2035",
            "author": "Luffy",
        },
    )
    new_meta = client.get(
        f"/v1/studies/{study_id}",
        headers={"Authorization": f'Bearer {fred_credentials["access_token"]}'},
    )
    assert res.json() == new_meta.json()
    assert new_meta.json()["status"] == "copied"
    assert new_meta.json()["name"] == "STA-mini-copy"
    assert new_meta.json()["horizon"] == "2035"


def test_matrix(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    matrix = [[1, 2], [3, 4]]

    res = client.post(
        "/v1/matrix",
        headers=admin_headers,
        json=matrix,
    )

    assert res.status_code == 200

    res = client.get(f"/v1/matrix/{res.json()}", headers=admin_headers)

    assert res.status_code == 200
    stored = res.json()
    assert stored["created_at"] > 0
    assert stored["id"] != ""

    matrix_id = stored["id"]

    res = client.get(f"/v1/matrix/{matrix_id}/download", headers=admin_headers)
    assert res.status_code == 200

    res = client.post(
        "/v1/matrixdataset",
        json={
            "metadata": {
                "name": "mydataset",
                "groups": [],
                "public": False,
            },
            "matrices": [{"id": matrix_id, "name": "mymatrix"}],
        },
        headers=admin_headers,
    )
    assert res.status_code == 200

    res = client.get("/v1/matrixdataset/_search?name=myda", headers=admin_headers)
    results = res.json()
    assert len(results) == 1
    assert len(results[0]["matrices"]) == 1
    assert results[0]["matrices"][0]["id"] == matrix_id

    dataset_id = results[0]["id"]
    res = client.get(f"/v1/matrixdataset/{dataset_id}/download", headers=admin_headers)
    assert res.status_code == 200

    res = client.delete(f"/v1/matrixdataset/{dataset_id}", headers=admin_headers)
    assert res.status_code == 200


def test_area_management(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    created = client.post("/v1/studies?name=foo", headers=admin_headers)
    study_id = created.json()
    res_areas = client.get(f"/v1/studies/{study_id}/areas", headers=admin_headers)
    assert res_areas.json() == [
        {
            "id": "all areas",
            "metadata": {"country": None, "tags": []},
            "name": "All areas",
            "set": [],
            "thermals": None,
            "type": "DISTRICT",
        }
    ]

    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers=admin_headers,
        json={
            "name": "area 1",
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR", "tags": ["a"]},
        },
    )
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers=admin_headers,
        json={
            "name": "area 1",
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR"},
        },
    )
    assert res.status_code == 500
    assert res.json() == {
        "description": "Area 'area 1' already exists and could not be created",
        "exception": "CommandApplicationError",
    }

    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=admin_headers,
        json={
            "name": "area 2",
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_THERMAL_CLUSTER.value,
                "args": {
                    "area_id": "area 1",
                    "cluster_name": "cluster 1",
                    "parameters": {},
                },
            }
        ],
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_THERMAL_CLUSTER.value,
                "args": {
                    "area_id": "area 2",
                    "cluster_name": "cluster 2",
                    "parameters": {},
                },
            }
        ],
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_RENEWABLES_CLUSTER.value,
                "args": {
                    "area_id": "area 1",
                    "cluster_name": "cluster renewable 1",
                    "parameters": {},
                },
            }
        ],
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_RENEWABLES_CLUSTER.value,
                "args": {
                    "area_id": "area 2",
                    "cluster_name": "cluster renewable 2",
                    "parameters": {},
                },
            }
        ],
    )

    res = client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 1",
                    "enabled": True,
                    "time_step": BindingConstraintFrequency.HOURLY.value,
                    "operator": BindingConstraintOperator.LESS.value,
                    "coeffs": {"area 1.cluster 1": [2.0, 4]},
                },
            }
        ],
    )
    res.raise_for_status()

    res = client.post(
        f"/v1/studies/{study_id}/commands",
        headers=admin_headers,
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 2",
                    "enabled": True,
                    "time_step": BindingConstraintFrequency.HOURLY.value,
                    "operator": BindingConstraintOperator.LESS.value,
                    "coeffs": {},
                },
            }
        ],
    )
    res.raise_for_status()

    res_areas = client.get(f"/v1/studies/{study_id}/areas", headers=admin_headers)
    assert res_areas.json() == [
        {
            "id": "area 1",
            "metadata": {"country": "FR", "tags": ["a"]},
            "name": "area 1",
            "set": None,
            "thermals": [
                {
                    "code-oi": None,
                    "enabled": True,
                    "group": None,
                    "id": "cluster 1",
                    "marginal-cost": None,
                    "market-bid-cost": None,
                    "min-down-time": None,
                    "min-stable-power": None,
                    "min-up-time": None,
                    "name": "cluster 1",
                    "nominalcapacity": 0,
                    "spinning": None,
                    "spread-cost": None,
                    "type": None,
                    "unitcount": 0,
                }
            ],
            "type": "AREA",
        },
        {
            "id": "area 2",
            "metadata": {"country": "DE", "tags": []},
            "name": "area 2",
            "set": None,
            "thermals": [
                {
                    "code-oi": None,
                    "enabled": True,
                    "group": None,
                    "id": "cluster 2",
                    "marginal-cost": None,
                    "market-bid-cost": None,
                    "min-down-time": None,
                    "min-stable-power": None,
                    "min-up-time": None,
                    "name": "cluster 2",
                    "nominalcapacity": 0,
                    "spinning": None,
                    "spread-cost": None,
                    "type": None,
                    "unitcount": 0,
                }
            ],
            "type": "AREA",
        },
        {
            "id": "all areas",
            "metadata": {"country": None, "tags": []},
            "name": "All areas",
            "set": ANY,  # because some time the order is not the same
            "thermals": None,
            "type": "DISTRICT",
        },
    ]

    client.post(
        f"/v1/studies/{study_id}/links",
        headers=admin_headers,
        json={
            "area1": "area 1",
            "area2": "area 2",
        },
    )
    res_links = client.get(f"/v1/studies/{study_id}/links?with_ui=true", headers=admin_headers)
    assert res_links.json() == [
        {
            "area1": "area 1",
            "area2": "area 2",
            "ui": {"color": "112,112,112", "style": "plain", "width": 1.0},
        }
    ]

    # -- `layers` integration tests

    res = client.get(f"/v1/studies/{study_id}/layers", headers=admin_headers)
    assert res.json() == [LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict()]

    res = client.post(f"/v1/studies/{study_id}/layers?name=test", headers=admin_headers)
    assert res.json() == "1"

    res = client.get(f"/v1/studies/{study_id}/layers", headers=admin_headers)
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test", areas=[]).dict(),
    ]

    res = client.put(f"/v1/studies/{study_id}/layers/1?name=test2", headers=admin_headers)
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 1"], headers=admin_headers)
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 2"], headers=admin_headers)
    res = client.get(f"/v1/studies/{study_id}/layers", headers=admin_headers)
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test2", areas=["area 2"]).dict(),
    ]

    # Delete the layer '1' that has 1 area
    res = client.delete(f"/v1/studies/{study_id}/layers/1", headers=admin_headers)
    assert res.status_code == HTTPStatus.NO_CONTENT

    # Ensure the layer is deleted
    res = client.get(f"/v1/studies/{study_id}/layers", headers=admin_headers)
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
    ]

    # Create the layer again without areas
    res = client.post(f"/v1/studies/{study_id}/layers?name=test2", headers=admin_headers)
    assert res.json() == "1"

    # Delete the layer with no areas
    res = client.delete(f"/v1/studies/{study_id}/layers/1", headers=admin_headers)
    assert res.status_code == HTTPStatus.NO_CONTENT

    # Ensure the layer is deleted
    res = client.get(f"/v1/studies/{study_id}/layers", headers=admin_headers)
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
    ]

    # Try to delete a non-existing layer
    res = client.delete(f"/v1/studies/{study_id}/layers/1", headers=admin_headers)
    assert res.status_code == HTTPStatus.NOT_FOUND

    # Try to delete the layer 'All'
    res = client.delete(f"/v1/studies/{study_id}/layers/0", headers=admin_headers)
    assert res.status_code == HTTPStatus.BAD_REQUEST

    # -- `district` integration tests

    res = client.post(
        f"/v1/studies/{study_id}/districts",
        headers=admin_headers,
        json={
            "name": "District 1",
            "output": True,
            "comments": "My District",
            "areas": [],
        },
    )
    assert res.status_code == 200
    assert res.json() == {
        "id": "district 1",
        "name": "District 1",
        "output": True,
        "comments": "My District",
        "areas": [],
    }

    res = client.put(
        f"/v1/studies/{study_id}/districts/district%201",
        headers=admin_headers,
        json={
            "name": "District 1",
            "output": True,
            "comments": "Your District",
            "areas": [],
        },
    )
    assert res.status_code == 200

    res = client.get(f"/v1/studies/{study_id}/districts", headers=admin_headers)
    assert res.status_code == 200
    actual = res.json()
    actual[0]["areas"].sort()
    actual[1]["areas"].sort()
    assert actual == [
        {
            "id": "all areas",
            "name": "All areas",
            "output": False,
            "comments": "Spatial aggregates on all areas",
            "areas": ["area 1", "area 2"],
        },
        {
            "id": "district 1",
            "name": "District 1",
            "output": True,
            "comments": "Your District",
            "areas": [],
        },
    ]

    res = client.delete(f"/v1/studies/{study_id}/districts/district%201", headers=admin_headers)
    assert res.status_code == 200

    # Optimization form

    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form", headers=admin_headers)
    res_optimization_config_json = res_optimization_config.json()
    assert res_optimization_config_json == {
        "bindingConstraints": True,
        "hurdleCosts": True,
        "transmissionCapacities": TransmissionCapacities.LOCAL_VALUES.value,
        "thermalClustersMinStablePower": True,
        "thermalClustersMinUdTime": True,
        "dayAheadReserve": True,
        "primaryReserve": True,
        "strategicReserve": True,
        "spinningReserve": True,
        "exportMps": False,
        "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.ERROR_VERBOSE.value,
        "simplexOptimizationRange": SimplexOptimizationRange.WEEK.value,
    }

    client.put(
        f"/v1/studies/{study_id}/config/optimization/form",
        headers=admin_headers,
        json={
            "strategicReserve": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
            "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
        },
    )
    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form", headers=admin_headers)
    res_optimization_config_json = res_optimization_config.json()
    assert res_optimization_config_json == {
        "bindingConstraints": True,
        "hurdleCosts": True,
        "transmissionCapacities": TransmissionCapacities.LOCAL_VALUES.value,
        "thermalClustersMinStablePower": True,
        "thermalClustersMinUdTime": True,
        "dayAheadReserve": True,
        "primaryReserve": True,
        "strategicReserve": False,
        "spinningReserve": True,
        "exportMps": False,
        "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
        "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
    }

    # Adequacy patch form

    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form", headers=admin_headers)
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": True,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": PriceTakingOrder.DENS.value,
        "thresholdInitiateCurtailmentSharingRule": 0.0,
        "thresholdDisplayLocalMatchingRuleViolations": 0.0,
        "thresholdCsrVariableBoundsRelaxation": 3,
    }

    client.put(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        headers=admin_headers,
        json={
            "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
            "priceTakingOrder": PriceTakingOrder.LOAD.value,
            "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        },
    )
    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form", headers=admin_headers)
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": PriceTakingOrder.LOAD.value,
        "thresholdInitiateCurtailmentSharingRule": 0.0,
        "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        "thresholdCsrVariableBoundsRelaxation": 3,
    }

    # General form

    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form", headers=admin_headers)
    res_general_config_json = res_general_config.json()
    assert res_general_config_json == {
        "mode": "Economy",
        "firstDay": 1,
        "lastDay": 365,
        "horizon": "",
        "firstMonth": "january",
        "firstWeekDay": "Monday",
        "firstJanuary": "Monday",
        "leapYear": False,
        "nbYears": 1,
        "buildingMode": "Automatic",
        "selectionMode": False,
        "yearByYear": False,
        "simulationSynthesis": True,
        "mcScenario": False,
        "geographicTrimming": False,
        "thematicTrimming": False,
    }

    client.put(
        f"/v1/studies/{study_id}/config/general/form",
        headers=admin_headers,
        json={
            "mode": Mode.ADEQUACY.value,
            "firstDay": 2,
            "lastDay": 299,
            "leapYear": True,
        },
    )
    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form", headers=admin_headers)
    res_general_config_json = res_general_config.json()
    assert res_general_config_json == {
        "mode": Mode.ADEQUACY.value,
        "firstDay": 2,
        "lastDay": 299,
        "horizon": "",
        "firstMonth": "january",
        "firstWeekDay": "Monday",
        "firstJanuary": "Monday",
        "leapYear": True,
        "nbYears": 1,
        "buildingMode": "Automatic",
        "selectionMode": False,
        "yearByYear": False,
        "simulationSynthesis": True,
        "mcScenario": False,
        "geographicTrimming": False,
        "thematicTrimming": False,
    }

    # Thematic trimming form

    res_thematic_trimming_config = client.get(
        f"/v1/studies/{study_id}/config/thematictrimming/form", headers=admin_headers
    )
    res_thematic_trimming_config_json = res_thematic_trimming_config.json()
    assert res_thematic_trimming_config_json == {
        "ovCost": True,
        "opCost": True,
        "mrgPrice": True,
        "co2Emis": True,
        "dtgByPlant": True,
        "balance": True,
        "rowBal": True,
        "psp": True,
        "miscNdg": True,
        "load": True,
        "hRor": True,
        "wind": True,
        "solar": True,
        "nuclear": True,
        "lignite": True,
        "coal": True,
        "gas": True,
        "oil": True,
        "mixFuel": True,
        "miscDtg": True,
        "hStor": True,
        "hPump": True,
        "hLev": True,
        "hInfl": True,
        "hOvfl": True,
        "hVal": True,
        "hCost": True,
        "unspEnrg": True,
        "spilEnrg": True,
        "lold": True,
        "lolp": True,
        "avlDtg": True,
        "dtgMrg": True,
        "maxMrg": True,
        "npCost": True,
        "npCostByPlant": True,
        "nodu": True,
        "noduByPlant": True,
        "flowLin": True,
        "ucapLin": True,
        "loopFlow": True,
        "flowQuad": True,
        "congFeeAlg": True,
        "congFeeAbs": True,
        "margCost": True,
        "congProbPlus": True,
        "congProbMinus": True,
        "hurdleCost": True,
        "resGenerationByPlant": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "windOffshore": True,
        "windOnshore": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "renw1": True,
        "renw2": True,
        "renw3": True,
        "renw4": True,
        "dens": True,
        "profitByPlant": True,
    }

    client.put(
        f"/v1/studies/{study_id}/config/thematictrimming/form",
        headers=admin_headers,
        json={
            "ovCost": False,
            "opCost": True,
            "mrgPrice": True,
            "co2Emis": True,
            "dtgByPlant": True,
            "balance": True,
            "rowBal": True,
            "psp": True,
            "miscNdg": True,
            "load": True,
            "hRor": True,
            "wind": True,
            "solar": True,
            "nuclear": True,
            "lignite": True,
            "coal": True,
            "gas": True,
            "oil": True,
            "mixFuel": True,
            "miscDtg": True,
            "hStor": True,
            "hPump": True,
            "hLev": True,
            "hInfl": True,
            "hOvfl": True,
            "hVal": False,
            "hCost": True,
            "unspEnrg": True,
            "spilEnrg": True,
            "lold": True,
            "lolp": True,
            "avlDtg": True,
            "dtgMrg": True,
            "maxMrg": True,
            "npCost": True,
            "npCostByPlant": True,
            "nodu": True,
            "noduByPlant": True,
            "flowLin": True,
            "ucapLin": True,
            "loopFlow": True,
            "flowQuad": True,
            "congFeeAlg": True,
            "congFeeAbs": True,
            "margCost": True,
            "congProbPlus": True,
            "congProbMinus": True,
            "hurdleCost": True,
            "resGenerationByPlant": True,
            "miscDtg2": True,
            "miscDtg3": True,
            "miscDtg4": True,
            "windOffshore": True,
            "windOnshore": True,
            "solarConcrt": True,
            "solarPv": True,
            "solarRooft": True,
            "renw1": True,
            "renw2": False,
            "renw3": True,
            "renw4": True,
            "dens": True,
            "profitByPlant": True,
        },
    )
    res_thematic_trimming_config = client.get(
        f"/v1/studies/{study_id}/config/thematictrimming/form", headers=admin_headers
    )
    res_thematic_trimming_config_json = res_thematic_trimming_config.json()
    assert res_thematic_trimming_config_json == {
        "ovCost": False,
        "opCost": True,
        "mrgPrice": True,
        "co2Emis": True,
        "dtgByPlant": True,
        "balance": True,
        "rowBal": True,
        "psp": True,
        "miscNdg": True,
        "load": True,
        "hRor": True,
        "wind": True,
        "solar": True,
        "nuclear": True,
        "lignite": True,
        "coal": True,
        "gas": True,
        "oil": True,
        "mixFuel": True,
        "miscDtg": True,
        "hStor": True,
        "hPump": True,
        "hLev": True,
        "hInfl": True,
        "hOvfl": True,
        "hVal": False,
        "hCost": True,
        "unspEnrg": True,
        "spilEnrg": True,
        "lold": True,
        "lolp": True,
        "avlDtg": True,
        "dtgMrg": True,
        "maxMrg": True,
        "npCost": True,
        "npCostByPlant": True,
        "nodu": True,
        "noduByPlant": True,
        "flowLin": True,
        "ucapLin": True,
        "loopFlow": True,
        "flowQuad": True,
        "congFeeAlg": True,
        "congFeeAbs": True,
        "margCost": True,
        "congProbPlus": True,
        "congProbMinus": True,
        "hurdleCost": True,
        "resGenerationByPlant": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "windOffshore": True,
        "windOnshore": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "renw1": True,
        "renw2": False,
        "renw3": True,
        "renw4": True,
        "dens": True,
        "profitByPlant": True,
    }

    # Properties form

    res_properties_config = client.get(f"/v1/studies/{study_id}/areas/area 1/properties/form", headers=admin_headers)
    res_properties_config_json = res_properties_config.json()
    res_properties_config_json["filterSynthesis"] = set(res_properties_config_json["filterSynthesis"])
    res_properties_config_json["filterByYear"] = set(res_properties_config_json["filterByYear"])
    assert res_properties_config_json == {
        "color": "230,108,44",
        "posX": 0.0,
        "posY": 0.0,
        "energyCostUnsupplied": 0.0,
        "energyCostSpilled": 0.0,
        "nonDispatchPower": True,
        "dispatchHydroPower": True,
        "otherDispatchPower": True,
        "filterSynthesis": {"hourly", "daily", "weekly", "monthly", "annual"},
        "filterByYear": {"hourly", "daily", "weekly", "monthly", "annual"},
        "adequacyPatchMode": AdequacyPatchMode.OUTSIDE.value,
    }

    client.put(
        f"/v1/studies/{study_id}/areas/area 1/properties/form",
        headers=admin_headers,
        json={
            "color": "123,108,96",
            "posX": 3.4,
            "posY": 9.0,
            "energyCostUnsupplied": 2.0,
            "energyCostSpilled": 4.0,
            "nonDispatchPower": False,
            "dispatchHydroPower": False,
            "otherDispatchPower": False,
            "filterSynthesis": ["monthly", "annual"],
            "filterByYear": ["hourly", "daily", "annual"],
            "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
        },
    )
    res_properties_config = client.get(f"/v1/studies/{study_id}/areas/area 1/properties/form", headers=admin_headers)
    res_properties_config_json = res_properties_config.json()
    res_properties_config_json["filterSynthesis"] = set(res_properties_config_json["filterSynthesis"])
    res_properties_config_json["filterByYear"] = set(res_properties_config_json["filterByYear"])
    assert res_properties_config_json == {
        "color": "123,108,96",
        "posX": 3.4,
        "posY": 9.0,
        "energyCostUnsupplied": 2.0,
        "energyCostSpilled": 4.0,
        "nonDispatchPower": False,
        "dispatchHydroPower": False,
        "otherDispatchPower": False,
        "filterSynthesis": {"monthly", "annual"},
        "filterByYear": {"hourly", "daily", "annual"},
        "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
    }

    # Hydro form

    res_hydro_config = client.put(
        f"/v1/studies/{study_id}/areas/area 1/hydro/form",
        headers=admin_headers,
        json={
            "interDailyBreakdown": 8,
            "intraDailyModulation": 7,
            "interMonthlyBreakdown": 5,
            "reservoir": True,
        },
    )
    assert res_hydro_config.status_code == 200

    res_hydro_config = client.get(f"/v1/studies/{study_id}/areas/area 1/hydro/form", headers=admin_headers)
    res_hydro_config_json = res_hydro_config.json()

    assert res_hydro_config_json == {
        "interDailyBreakdown": 8,
        "intraDailyModulation": 7,
        "interMonthlyBreakdown": 5,
        "reservoir": True,
        "reservoirCapacity": 0,
        "followLoad": True,
        "useWater": False,
        "hardBounds": False,
        "initializeReservoirDate": 0,
        "useHeuristic": True,
        "powerToLevel": False,
        "useLeeway": False,
        "leewayLow": 1,
        "leewayUp": 1,
        "pumpingEfficiency": 1,
    }

    # Time-series form

    res_ts_config = client.get(f"/v1/studies/{study_id}/config/timeseries/form", headers=admin_headers)
    res_ts_config_json = res_ts_config.json()
    assert res_ts_config_json == {
        "load": {
            "stochasticTsStatus": False,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "seasonCorrelation": "annual",
            "storeInInput": False,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "hydro": {
            "stochasticTsStatus": False,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "seasonCorrelation": "annual",
            "storeInInput": False,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "thermal": {
            "stochasticTsStatus": False,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "storeInInput": False,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "renewables": {
            "stochasticTsStatus": False,
            "intraModal": False,
            "interModal": False,
        },
        "ntc": {"stochasticTsStatus": False, "intraModal": False},
    }
    res_ts_config = client.put(
        f"/v1/studies/{study_id}/config/timeseries/form",
        headers=admin_headers,
        json={
            "thermal": {"stochasticTsStatus": True},
            "load": {
                "stochasticTsStatus": True,
                "storeInInput": True,
                "seasonCorrelation": "monthly",
            },
        },
    )
    res_ts_config = client.get(f"/v1/studies/{study_id}/config/timeseries/form", headers=admin_headers)
    res_ts_config_json = res_ts_config.json()
    assert res_ts_config_json == {
        "load": {
            "stochasticTsStatus": True,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "seasonCorrelation": "monthly",
            "storeInInput": True,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "hydro": {
            "stochasticTsStatus": False,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "seasonCorrelation": "annual",
            "storeInInput": False,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "thermal": {
            "stochasticTsStatus": True,
            "number": 1,
            "refresh": False,
            "refreshInterval": 100,
            "storeInInput": False,
            "storeInOutput": False,
            "intraModal": False,
            "interModal": False,
        },
        "renewables": {
            "stochasticTsStatus": False,
            "intraModal": False,
            "interModal": False,
        },
        "ntc": {"stochasticTsStatus": False, "intraModal": False},
    }

    # --- TableMode START ---

    table_mode_url = f"/v1/studies/{study_id}/tablemode"

    # Table Mode - Area

    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.AREA.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.AREA]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1": {
            "nonDispatchablePower": False,
            "dispatchableHydroPower": False,
            "otherDispatchablePower": False,
            "averageUnsuppliedEnergyCost": 2.0,
            "spreadUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 4.0,
            "spreadSpilledEnergyCost": 0.0,
            "filterSynthesis": "monthly, annual",
            "filterYearByYear": "hourly, daily, annual",
            "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
        },
        "area 2": {
            "nonDispatchablePower": True,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "averageUnsuppliedEnergyCost": 0.0,
            "spreadUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 0.0,
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "adequacyPatchMode": AdequacyPatchMode.OUTSIDE.value,
        },
    }

    client.put(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.AREA.value,
        },
        json={
            "area 1": {
                "nonDispatchablePower": True,
                "spreadSpilledEnergyCost": 1.1,
                "filterYearByYear": "monthly, annual",
                "adequacyPatchMode": AdequacyPatchMode.OUTSIDE.value,
            },
            "area 2": {
                "nonDispatchablePower": False,
                "spreadSpilledEnergyCost": 3.0,
                "filterSynthesis": "hourly",
                "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.AREA.value,
            "columns": ",".join(list(FIELDS_INFO_BY_TYPE[TableTemplateType.AREA])),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1": {
            "nonDispatchablePower": True,
            "dispatchableHydroPower": False,
            "otherDispatchablePower": False,
            "averageUnsuppliedEnergyCost": 2.0,
            "spreadUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 4.0,
            "spreadSpilledEnergyCost": 1.1,
            "filterSynthesis": "monthly, annual",
            "filterYearByYear": "monthly, annual",
            "adequacyPatchMode": AdequacyPatchMode.OUTSIDE.value,
        },
        "area 2": {
            "nonDispatchablePower": False,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "averageUnsuppliedEnergyCost": 0.0,
            "spreadUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 3.0,
            "filterSynthesis": "hourly",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
        },
    }

    # Table Mode - Link

    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.LINK.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.LINK]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / area 2": {
            "hurdlesCost": False,
            "loopFlow": False,
            "usePhaseShifter": False,
            "transmissionCapacities": "enabled",
            "assetType": "ac",
            "linkStyle": "plain",
            "linkWidth": True,
            "displayComments": True,
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
        }
    }

    client.put(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.LINK.value,
        },
        json={
            "area 1 / area 2": {
                "hurdlesCost": True,
                "transmissionCapacities": TransmissionCapacity.IGNORE.value,
                "assetType": AssetType.GAZ.value,
                "filterSynthesis": "daily,annual",
            }
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.LINK.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.LINK]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / area 2": {
            "hurdlesCost": True,
            "loopFlow": False,
            "usePhaseShifter": False,
            "transmissionCapacities": "ignore",
            "assetType": "gaz",
            "linkStyle": "plain",
            "linkWidth": True,
            "displayComments": True,
            "filterSynthesis": "daily,annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
        }
    }

    # Table Mode - Cluster

    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.CLUSTER.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.CLUSTER]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / cluster 1": {
            "group": "",
            "enabled": True,
            "mustRun": False,
            "unitCount": 0,
            "nominalCapacity": 0,
            "minStablePower": 0,
            "spinning": 0,
            "minUpTime": 1,
            "minDownTime": 1,
            "co2": 0,
            "marginalCost": 0,
            "fixedCost": 0,
            "startupCost": 0,
            "marketBidCost": 0,
            "spreadCost": 0,
            "tsGen": "use global",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
        },
        "area 2 / cluster 2": {
            "group": "",
            "enabled": True,
            "mustRun": False,
            "unitCount": 0,
            "nominalCapacity": 0,
            "minStablePower": 0,
            "spinning": 0,
            "minUpTime": 1,
            "minDownTime": 1,
            "co2": 0,
            "marginalCost": 0,
            "fixedCost": 0,
            "startupCost": 0,
            "marketBidCost": 0,
            "spreadCost": 0,
            "tsGen": "use global",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
        },
    }

    client.put(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.CLUSTER.value,
        },
        json={
            "area 1 / cluster 1": {
                "enabled": False,
                "unitCount": 3,
                "spinning": 8,
                "tsGen": LocalTSGenerationBehavior.FORCE_GENERATION.value,
                "lawPlanned": LawOption.GEOMETRIC.value,
            },
            "area 2 / cluster 2": {
                "nominalCapacity": 2,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.CLUSTER.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.CLUSTER]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / cluster 1": {
            "group": "",
            "enabled": False,
            "mustRun": False,
            "unitCount": 3,
            "nominalCapacity": 0,
            "minStablePower": 0,
            "spinning": 8,
            "minUpTime": 1,
            "minDownTime": 1,
            "co2": 0,
            "marginalCost": 0,
            "fixedCost": 0,
            "startupCost": 0,
            "marketBidCost": 0,
            "spreadCost": 0,
            "tsGen": "force generation",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "geometric",
        },
        "area 2 / cluster 2": {
            "group": "",
            "enabled": True,
            "mustRun": False,
            "unitCount": 0,
            "nominalCapacity": 2,
            "minStablePower": 0,
            "spinning": 0,
            "minUpTime": 1,
            "minDownTime": 1,
            "co2": 0,
            "marginalCost": 0,
            "fixedCost": 0,
            "startupCost": 0,
            "marketBidCost": 0,
            "spreadCost": 0,
            "tsGen": "use global",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
        },
    }

    # Table Mode - Renewable

    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.RENEWABLE.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.RENEWABLE]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / cluster renewable 1": {
            "group": "",
            "tsInterpretation": TimeSeriesInterpretation.POWER_GENERATION.value,
            "enabled": True,
            "unitCount": 0,
            "nominalCapacity": 0,
        },
        "area 2 / cluster renewable 2": {
            "group": "",
            "tsInterpretation": TimeSeriesInterpretation.POWER_GENERATION.value,
            "enabled": True,
            "unitCount": 0,
            "nominalCapacity": 0,
        },
    }

    client.put(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.RENEWABLE.value,
        },
        json={
            "area 1 / cluster renewable 1": {
                "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR.value,
                "enabled": False,
            },
            "area 2 / cluster renewable 2": {
                "unitCount": 2,
                "nominalCapacity": 13,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.RENEWABLE.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.RENEWABLE]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1 / cluster renewable 1": {
            "group": "",
            "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR.value,
            "enabled": False,
            "unitCount": 0,
            "nominalCapacity": 0,
        },
        "area 2 / cluster renewable 2": {
            "group": "",
            "tsInterpretation": TimeSeriesInterpretation.POWER_GENERATION.value,
            "enabled": True,
            "unitCount": 2,
            "nominalCapacity": 13,
        },
    }

    # Table Mode - Binding Constraint

    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.BINDING_CONSTRAINT]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "binding constraint 1": {
            "enabled": True,
            "type": BindingConstraintFrequency.HOURLY.value,
            "operator": BindingConstraintOperator.LESS.value,
        },
        "binding constraint 2": {
            "enabled": True,
            "type": BindingConstraintFrequency.HOURLY.value,
            "operator": BindingConstraintOperator.LESS.value,
        },
    }

    client.put(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT.value,
        },
        json={
            "binding constraint 1": {
                "enabled": False,
                "operator": BindingConstraintOperator.BOTH.value,
            },
            "binding constraint 2": {
                "type": BindingConstraintFrequency.WEEKLY.value,
                "operator": BindingConstraintOperator.EQUAL.value,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers=admin_headers,
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT.value,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.BINDING_CONSTRAINT]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "binding constraint 1": {
            "enabled": False,
            "type": BindingConstraintFrequency.HOURLY.value,
            "operator": BindingConstraintOperator.BOTH.value,
        },
        "binding constraint 2": {
            "enabled": True,
            "type": BindingConstraintFrequency.WEEKLY.value,
            "operator": BindingConstraintOperator.EQUAL.value,
        },
    }

    res = client.get(f"/v1/studies/{study_id}/bindingconstraints/binding constraint 1", headers=admin_headers)
    binding_constraint_1 = res.json()
    assert res.status_code == 200

    constraint = binding_constraint_1["constraints"][0]
    assert constraint["id"] == "area 1.cluster 1"
    assert constraint["weight"] == 2.0
    assert constraint["offset"] == 4.0

    # --- TableMode END ---

    # Renewable form

    res = client.put(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
        headers=admin_headers,
        json={
            "name": "cluster renewable 1 renamed",
            "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR,
            "unitCount": 9,
            "enabled": False,
            "nominalCapacity": 3,
        },
    )
    assert res.status_code == 200, res.json()

    res = client.get(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
        headers=admin_headers,
    )
    expected = {
        "enabled": False,
        "group": RenewableClusterGroup.OTHER1,  # Default group used when not specified.
        "id": "cluster renewable 1",
        "name": "cluster renewable 1 renamed",
        "nominalCapacity": 3.0,
        "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR,
        "unitCount": 9,
    }
    assert res.status_code == 200, res.json()
    assert res.json() == expected

    # Thermal form

    obj = {
        "group": "Lignite",
        "name": "cluster 1 renamed",
        "unitCount": 3,
        "enabled": False,
        "nominalCapacity": 3,
        "genTs": "use global",
        "minStablePower": 3,
        "minUpTime": 3,
        "minDownTime": 3,
        "mustRun": False,
        "spinning": 3,
        "volatilityForced": 0.3,
        "volatilityPlanned": 0.3,
        "lawForced": "uniform",
        "lawPlanned": "uniform",
        "marginalCost": 3,
        "spreadCost": 3,
        "fixedCost": 3,
        "startupCost": 3,
        "marketBidCost": 3,
        "co2": 3,
        "so2": 2,
        "nh3": 2,
        "nox": 4,
        "nmvoc": 5,
        "pm25": 11.3,
        "pm5": 7,
        "pm10": 9,
        "op1": 0.5,
        "op2": 39,
        "op3": 3,
        "op4": 2.4,
        "op5": 0,
    }
    res = client.put(
        # This URL is deprecated, but we must check it for backward compatibility.
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
        headers=admin_headers,
        json=obj,
    )
    assert res.status_code == 200, res.json()

    res = client.get(
        # This URL is deprecated, but we must check it for backward compatibility.
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
        headers=admin_headers,
    )
    assert res.status_code == 200, res.json()
    assert res.json() == {"id": "cluster 1", **obj}

    # Links

    client.delete(f"/v1/studies/{study_id}/links/area%201/area%202", headers=admin_headers)
    res_links = client.get(f"/v1/studies/{study_id}/links", headers=admin_headers)
    assert res_links.json() == []

    res = client.put(
        f"/v1/studies/{study_id}/areas/area%201/ui",
        headers=admin_headers,
        json={"x": 100, "y": 100, "color_rgb": [255, 0, 100]},
    )
    res = client.put(
        f"/v1/studies/{study_id}/areas/area%202/ui?layer=1",
        headers=admin_headers,
        json={"x": 105, "y": 105, "color_rgb": [255, 10, 100]},
    )
    assert res.status_code == 200
    res_ui = client.get(f"/v1/studies/{study_id}/areas?ui=true", headers=admin_headers)
    assert res_ui.json() == {
        "area 1": {
            "ui": {
                "x": 100,
                "y": 100,
                "color_r": 255,
                "color_g": 0,
                "color_b": 100,
                "layers": 0,
            },
            "layerX": {"0": 100},
            "layerY": {"0": 100},
            "layerColor": {"0": "255 , 0 , 100"},
        },
        "area 2": {
            "ui": {
                "x": 0,
                "y": 0,
                "color_r": 230,
                "color_g": 108,
                "color_b": 44,
                "layers": "0 1",
            },
            "layerX": {"0": 0, "1": 105},
            "layerY": {"0": 0, "1": 105},
            "layerColor": {"0": "230 , 108 , 44", "1": "255 , 10 , 100"},
        },
    }

    result = client.delete(f"/v1/studies/{study_id}/areas/area%201", headers=admin_headers)
    assert result.status_code == 200
    res_areas = client.get(f"/v1/studies/{study_id}/areas", headers=admin_headers)
    assert res_areas.json() == [
        {
            "id": "area 2",
            "metadata": {"country": "DE", "tags": []},
            "name": "area 2",
            "set": None,
            "thermals": [
                {
                    "code-oi": None,
                    "enabled": True,
                    "group": None,
                    "id": "cluster 2",
                    "marginal-cost": None,
                    "market-bid-cost": None,
                    "min-down-time": None,
                    "min-stable-power": None,
                    "min-up-time": None,
                    "name": "cluster 2",
                    "nominalcapacity": 2,
                    "spinning": None,
                    "spread-cost": None,
                    "type": None,
                    "unitcount": 0,
                }
            ],
            "type": "AREA",
        },
        {
            "id": "all areas",
            "metadata": {"country": None, "tags": []},
            "name": "All areas",
            "set": ["area 2"],
            "thermals": None,
            "type": "DISTRICT",
        },
    ]


def test_archive(client: TestClient, admin_access_token: str, study_id: str, tmp_path: Path) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    study_res = client.post("/v1/studies?name=foo", headers=admin_headers)
    study_id = study_res.json()

    res = client.put(f"/v1/studies/{study_id}/archive", headers=admin_headers)
    assert res.status_code == 200
    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
            headers=admin_headers,
        ).json()["status"]
        == 3
    )

    res = client.get(f"/v1/studies/{study_id}", headers=admin_headers)
    assert res.json()["archived"]
    assert (tmp_path / "archive_dir" / f"{study_id}.zip").exists()

    res = client.put(f"/v1/studies/{study_id}/unarchive", headers=admin_headers)

    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
            headers=admin_headers,
        ).json()["status"]
        == 3
    )

    res = client.get(f"/v1/studies/{study_id}", headers=admin_headers)
    assert not res.json()["archived"]
    assert not (tmp_path / "archive_dir" / f"{study_id}.zip").exists()


def test_maintenance(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create non admin user
    res = client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "user", "password": "user"},
    )
    assert res.status_code == 200

    res = client.post("/v1/login", json={"username": "user", "password": "user"})
    non_admin_credentials = res.json()

    # Test maintenance update utils function
    def set_maintenance(value: bool) -> None:
        # Set maintenance mode
        result = client.post(
            f"/v1/core/maintenance?maintenance={'true' if value else 'false'}",
            headers=admin_headers,
        )
        assert result.status_code == 200

        result = client.get(
            "/v1/core/maintenance",
            headers=admin_headers,
        )
        assert result.status_code == 200
        assert result.json() == value

    set_maintenance(True)
    set_maintenance(False)

    # Set maintenance mode when not admin
    res = client.post(
        "/v1/core/maintenance?maintenance=true",
        headers={"Authorization": f'Bearer {non_admin_credentials["access_token"]}'},
    )
    assert res.status_code == 403

    # Set message info
    message = "Hey"
    res = client.post(
        "/v1/core/maintenance/message",
        headers=admin_headers,
        json=message,
    )
    assert res.status_code == 200

    # Set message info when not admin
    res = client.get("/v1/core/maintenance/message", headers=admin_headers)
    assert res.status_code == 200
    assert res.json() == message


def test_import(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    zip_path = ASSETS_DIR / "STA-mini.zip"
    seven_zip_path = ASSETS_DIR / "STA-mini.7z"

    # Admin who belongs to a group imports a study
    uuid = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(zip_path.read_bytes())},
        headers=admin_headers,
    ).json()
    res = client.get(f"v1/studies/{uuid}", headers=admin_headers).json()
    assert res["groups"] == [{"id": "admin", "name": "admin"}]
    assert res["public_mode"] == PublicMode.NONE

    # Create user George who belongs to no group
    client.post(
        "/v1/users",
        headers=admin_headers,
        json={"name": "George", "password": "mypass"},
    )
    res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
    george_credentials = res.json()

    # George imports a study
    georges_headers = {"Authorization": f'Bearer {george_credentials["access_token"]}'}
    uuid = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(zip_path.read_bytes())},
        headers=georges_headers,
    ).json()
    res = client.get(f"v1/studies/{uuid}", headers=georges_headers).json()
    assert res["groups"] == []
    assert res["public_mode"] == PublicMode.READ

    # Study importer works for 7z files
    res = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(seven_zip_path.read_bytes())},
        headers=admin_headers,
    )
    assert res.status_code == 201

    # tests outputs import for .zip
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    client.post(
        f"/v1/studies/{study_id}/output",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 6

    # tests outputs import for .7z
    output_path_seven_zip = ASSETS_DIR / "output_adq.7z"
    client.post(
        f"/v1/studies/{study_id}/output",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        files={"output": io.BytesIO(output_path_seven_zip.read_bytes())},
    )
    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert len(res.json()) == 7

    # test matrices import for .zip and .7z files
    matrices_zip_path = ASSETS_DIR / "matrices.zip"
    res_zip = client.post(
        "/v1/matrix/_import",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        files={"file": (matrices_zip_path.name, io.BytesIO(matrices_zip_path.read_bytes()), "application/zip")},
    )
    matrices_seven_zip_path = ASSETS_DIR / "matrices.7z"
    res_seven_zip = client.post(
        "/v1/matrix/_import",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        files={
            "file": (matrices_seven_zip_path.name, io.BytesIO(matrices_seven_zip_path.read_bytes()), "application/zip")
        },
    )
    for res in [res_zip, res_seven_zip]:
        assert res.status_code == 200
        result = res.json()
        assert len(result) == 2
        assert result[0]["name"] == "fr.txt"
        assert result[1]["name"] == "it.txt"


def test_copy(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Copy a study with admin user who belongs to a group
    copied = client.post(f"/v1/studies/{study_id}/copy?dest=copied&use_task=false", headers=admin_headers)
    assert copied.status_code == 201
    # asserts that it has admin groups and PublicMode to NONE
    res = client.get(f"/v1/studies/{copied.json()}", headers=admin_headers).json()
    assert res["groups"] == [{"id": "admin", "name": "admin"}]
    assert res["public_mode"] == PublicMode.NONE

    # Connect with user George who belongs to no group
    res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
    george_credentials = res.json()

    # George copies a study
    copied = client.post(
        f"/v1/studies/{study_id}/copy?dest=copied&use_task=false",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert copied.status_code == 201
    # asserts that it has no groups and PublicMode to READ
    res = client.get(f"/v1/studies/{copied.json()}", headers=admin_headers).json()
    assert res["groups"] == []
    assert res["public_mode"] == PublicMode.READ


def test_download_matrices(client: TestClient, admin_access_token: str, study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # todo: replacer ce test dans un autre fichier

    # =============================
    #  STUDIES PREPARATION
    # =============================

    # Manage parent study
    copied = client.post(f"/v1/studies/{study_id}/copy?dest=copied&use_task=false", headers=admin_headers)
    parent_id = copied.json()

    # Create Variant
    res = client.post(
        f"/v1/studies/{parent_id}/variants",
        headers=admin_headers,
        params={"name": "variant_1"},
    )
    assert res.status_code == 200
    variant_id = res.json()

    # Create a new area to implicitly create normalized matrices
    area_name = "new_area"
    res = client.post(
        f"/v1/studies/{variant_id}/areas",
        headers=admin_headers,
        json={"name": area_name, "type": "AREA", "metadata": {"country": "FR"}},
    )
    assert res.status_code in {200, 201}

    # Change study start_date
    res = client.put(
        f"/v1/studies/{variant_id}/config/general/form", json={"firstMonth": "july"}, headers=admin_headers
    )
    assert res.status_code == 200

    # Really generates the snapshot
    client.get(f"/v1/studies/{variant_id}/areas", headers=admin_headers)
    assert res.status_code == 200

    # =============================
    #  TESTS MATRIX CONSISTENCY FOR RAW AND VARIANT STUDY
    # =============================

    raw_matrix_path = r"input/load/series/load_de"
    variant_matrix_path = f"input/load/series/load_{area_name}"
    fake_str = "fake_str"

    for uuid, path in zip([parent_id, variant_id], [raw_matrix_path, variant_matrix_path]):
        # get downloaded bytes
        res = client.get(f"/v1/studies/{uuid}/raw/download?path={path}&format=xlsx", headers=admin_headers)
        assert res.status_code == 200

        # load into dataframe
        dataframe = pd.read_excel(io.BytesIO(res.content), index_col=0)

        # check time coherence
        generated_index = dataframe.index
        first_date = generated_index[0].to_pydatetime()
        second_date = generated_index[1].to_pydatetime()
        assert first_date.month == second_date.month == 1 if uuid == parent_id else 7
        assert first_date.day == second_date.day == 1
        assert first_date.hour == 0
        assert second_date.hour == 1

        # reformat into a json to help comparison
        new_cols = [int(col) for col in dataframe.columns]
        dataframe.columns = new_cols
        dataframe.index = range(len(dataframe))
        actual_matrix = dataframe.to_dict(orient="split")

        # asserts that the result is the same as the one we get with the classic get /raw endpoint
        res = client.get(f"/v1/studies/{uuid}/raw?path={path}&formatted=true", headers=admin_headers)
        expected_matrix = res.json()
        assert actual_matrix == expected_matrix

    # =============================
    # TEST OTHER PARAMETERS
    # =============================

    # test only few possibilities as each API call is quite long
    for header in [True, False]:
        index = not header
        res = client.get(
            f"/v1/studies/{parent_id}/raw/download?path={raw_matrix_path}&format=csv&header={header}&index={index}",
            headers=admin_headers,
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0 if index else None, header="infer" if header else None, sep="\t")
        first_index = dataframe.index[0]
        assert first_index == "2018-01-01 00:00:00" if index else first_index == 0
        assert isinstance(dataframe.columns[0], str) if header else isinstance(dataframe.columns[0], np.int64)

    # =============================
    #  ERRORS
    # =============================

    # fake study_id
    res = client.get(f"/v1/studies/{fake_str}/raw/download?path={raw_matrix_path}&format=csv", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["exception"] == "StudyNotFoundError"

    # fake path
    res = client.get(
        f"/v1/studies/{parent_id}/raw/download?path=input/links/de/{fake_str}&format=csv", headers=admin_headers
    )
    assert res.status_code == 404
    assert res.json()["exception"] == "ChildNotFoundError"

    # path that does not lead to a matrix
    res = client.get(
        f"/v1/studies/{parent_id}/raw/download?path=settings/generaldata&format=csv", headers=admin_headers
    )
    assert res.status_code == 404
    assert res.json()["exception"] == "IncorrectPathError"
    assert res.json()["description"] == "The path filled does not correspond to a matrix : settings/generaldata"

    # wrong format
    res = client.get(
        f"/v1/studies/{parent_id}/raw/download?path={raw_matrix_path}&format={fake_str}", headers=admin_headers
    )
    assert res.status_code == 422
    assert res.json()["exception"] == "RequestValidationError"
