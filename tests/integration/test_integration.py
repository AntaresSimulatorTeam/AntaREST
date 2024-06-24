import io
import os
from http import HTTPStatus
from pathlib import Path
from unittest.mock import ANY

from starlette.testclient import TestClient

from antarest.launcher.model import LauncherLoadDTO
from antarest.study.business.area_management import LayerInfoDTO
from antarest.study.business.general_management import Mode
from antarest.study.business.optimization_management import (
    SimplexOptimizationRange,
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_for


def test_main(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # create some new users
    # TODO check for bad username or empty password
    client.post(
        "/v1/users",
        json={"name": "George", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        json={"name": "Fred", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        json={"name": "Harry", "password": "mypass"},
    )
    res = client.get("/v1/users")
    assert len(res.json()) == 4

    # reject user with existing name creation
    res = client.post(
        "/v1/users",
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

    # Update the active ruleset
    active_ruleset_name = "ruleset test"
    res = client.post(
        f"/v1/studies/{study_id}/raw?path=settings/generaldata/general/active-rules-scenario",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json=active_ruleset_name.title(),  # ruleset names are case-insensitive
    )
    assert res.status_code == 204

    # scenario builder
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        json={
            active_ruleset_name: {
                "l": {"area1": {"0": 1}},
                "ntc": {"area1 / area2": {"1": 23}},
                "t": {"area1": {"thermal": {"1": 2}}},
                "hl": {"area1": {"0": 75}},
            },
            "Default Ruleset": {},  # should be removed
        },
    )
    assert res.status_code == 200, res.json()

    res = client.get(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
    )
    assert res.status_code == 200
    assert res.json() == {
        active_ruleset_name: {
            "l": {"area1": {"0": 1}},
            "ntc": {"area1 / area2": {"1": 23}},
            "t": {"area1": {"thermal": {"1": 2}}},
            "hl": {"area1": {"0": 75}},
        },
    }

    # Keys must be sorted in each section (to improve reading performance).
    assert list(res.json()[active_ruleset_name]) == ["hl", "l", "ntc", "t"]

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
        json={"name": "Weasley"},
    )
    res = client.get("/v1/groups")
    group_id = res.json()[1]["id"]
    client.post(
        "/v1/roles",
        json={"type": 40, "group_id": group_id, "identity_id": 3},
    )
    client.post(
        "/v1/roles",
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

    res = client.get("/v1/launcher/load")
    assert res.status_code == 200, res.json()
    launcher_load = LauncherLoadDTO(**res.json())
    assert launcher_load.allocated_cpu_rate == 100 / (os.cpu_count() or 1)
    assert launcher_load.cluster_load_rate == 100 / (os.cpu_count() or 1)
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


def test_matrix(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    matrix = [[1, 2], [3, 4]]

    res = client.post(
        "/v1/matrix",
        json=matrix,
    )

    assert res.status_code == 200

    res = client.get(f"/v1/matrix/{res.json()}")

    assert res.status_code == 200
    stored = res.json()
    assert stored["created_at"] > 0
    assert stored["id"] != ""

    matrix_id = stored["id"]

    res = client.get(f"/v1/matrix/{matrix_id}/download")
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
    )
    assert res.status_code == 200

    res = client.get("/v1/matrixdataset/_search?name=myda")
    results = res.json()
    assert len(results) == 1
    assert len(results[0]["matrices"]) == 1
    assert results[0]["matrices"][0]["id"] == matrix_id

    dataset_id = results[0]["id"]
    res = client.get(f"/v1/matrixdataset/{dataset_id}/download")
    assert res.status_code == 200

    res = client.delete(f"/v1/matrixdataset/{dataset_id}")
    assert res.status_code == 200


def test_area_management(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    created = client.post("/v1/studies", params={"name": "foo", "version": 870})
    study_id = created.json()
    res_areas = client.get(f"/v1/studies/{study_id}/areas")
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
        json={
            "name": "area 1",
            "type": "AREA",
            "metadata": {"country": "FR", "tags": ["a"]},
        },
    )
    assert res.status_code == 200, res.json()

    # Test area creation with duplicate name
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={
            "name": "Area 1",  # Same name but with different case
            "type": "AREA",
            "metadata": {"country": "FR"},
        },
    )
    assert res.status_code == 409, res.json()
    assert res.json() == {
        "description": "Area 'Area 1' already exists and could not be created",
        "exception": "DuplicateAreaName",
    }

    client.post(
        f"/v1/studies/{study_id}/areas",
        json={
            "name": "area 2",
            "type": "AREA",
            "metadata": {"country": "DE"},
        },
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
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
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 1",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "less",
                    "coeffs": {"area 1.cluster 1": [2.0, 4]},
                },
            }
        ],
    )
    res.raise_for_status()

    res = client.post(
        f"/v1/studies/{study_id}/commands",
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 2",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "less",
                    "coeffs": {},
                },
            }
        ],
    )
    res.raise_for_status()

    res_areas = client.get(f"/v1/studies/{study_id}/areas")
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
        json={
            "area1": "area 1",
            "area2": "area 2",
        },
    )
    res_links = client.get(f"/v1/studies/{study_id}/links?with_ui=true")
    assert res_links.json() == [
        {
            "area1": "area 1",
            "area2": "area 2",
            "ui": {"color": "112,112,112", "style": "plain", "width": 1.0},
        }
    ]

    # -- `layers` integration tests

    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict()]

    res = client.post(f"/v1/studies/{study_id}/layers?name=test")
    assert res.json() == "1"

    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test", areas=[]).dict(),
    ]

    res = client.put(f"/v1/studies/{study_id}/layers/1?name=test2")
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 1"])
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 2"])
    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test2", areas=["area 2"]).dict(),
    ]

    # Delete the layer '1' that has 1 area
    res = client.delete(f"/v1/studies/{study_id}/layers/1")
    assert res.status_code == HTTPStatus.NO_CONTENT

    # Ensure the layer is deleted
    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
    ]

    # Create the layer again without areas
    res = client.post(f"/v1/studies/{study_id}/layers?name=test2")
    assert res.json() == "1"

    # Delete the layer with no areas
    res = client.delete(f"/v1/studies/{study_id}/layers/1")
    assert res.status_code == HTTPStatus.NO_CONTENT

    # Ensure the layer is deleted
    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
    ]

    # Try to delete a non-existing layer
    res = client.delete(f"/v1/studies/{study_id}/layers/1")
    assert res.status_code == HTTPStatus.NOT_FOUND

    # Try to delete the layer 'All'
    res = client.delete(f"/v1/studies/{study_id}/layers/0")
    assert res.status_code == HTTPStatus.BAD_REQUEST

    # -- `district` integration tests

    res = client.post(
        f"/v1/studies/{study_id}/districts",
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
        json={
            "name": "District 1",
            "output": True,
            "comments": "Your District",
            "areas": [],
        },
    )
    assert res.status_code == 200

    res = client.get(f"/v1/studies/{study_id}/districts")
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

    res = client.delete(f"/v1/studies/{study_id}/districts/district%201")
    assert res.status_code == 200

    # Optimization form

    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form")
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
        json={
            "strategicReserve": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
            "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
        },
    )
    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form")
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

    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form")
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": True,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": "DENS",
        "thresholdInitiateCurtailmentSharingRule": 0.0,
        "thresholdDisplayLocalMatchingRuleViolations": 0.0,
        "thresholdCsrVariableBoundsRelaxation": 3,
    }

    client.put(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        json={
            "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
            "priceTakingOrder": "Load",
            "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        },
    )
    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form")
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": "Load",
        "thresholdInitiateCurtailmentSharingRule": 0.0,
        "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        "thresholdCsrVariableBoundsRelaxation": 3,
    }

    # General form

    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form")
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
        json={
            "mode": Mode.ADEQUACY.value,
            "firstDay": 2,
            "lastDay": 299,
            "leapYear": True,
        },
    )
    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form")
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

    res = client.get(f"/v1/studies/{study_id}/config/thematictrimming/form")
    obj = res.json()
    assert obj == {
        "avlDtg": True,
        "balance": True,
        "batteryInjection": True,
        "batteryLevel": True,
        "batteryWithdrawal": True,
        "co2Emis": True,
        "coal": True,
        "congFeeAbs": True,
        "congFeeAlg": True,
        "congProbMinus": True,
        "congProbPlus": True,
        "dens": True,
        "dtgByPlant": True,
        "dtgMrg": True,
        "flowLin": True,
        "flowQuad": True,
        "gas": True,
        "hCost": True,
        "hInfl": True,
        "hLev": True,
        "hOvfl": True,
        "hPump": True,
        "hRor": True,
        "hStor": True,
        "hVal": True,
        "hurdleCost": True,
        "lignite": True,
        "load": True,
        "lold": True,
        "lolp": True,
        "loopFlow": True,
        "margCost": True,
        "maxMrg": True,
        "miscDtg": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "miscNdg": True,
        "mixFuel": True,
        "mrgPrice": True,
        "nodu": True,
        "noduByPlant": True,
        "npCost": True,
        "npCostByPlant": True,
        "nuclear": True,
        "oil": True,
        "opCost": True,
        "other1Injection": True,
        "other1Level": True,
        "other1Withdrawal": True,
        "other2Injection": True,
        "other2Level": True,
        "other2Withdrawal": True,
        "other3Injection": True,
        "other3Level": True,
        "other3Withdrawal": True,
        "other4Injection": True,
        "other4Level": True,
        "other4Withdrawal": True,
        "other5Injection": True,
        "other5Level": True,
        "other5Withdrawal": True,
        "ovCost": True,
        "pondageInjection": True,
        "pondageLevel": True,
        "pondageWithdrawal": True,
        "profitByPlant": True,
        "psp": True,
        "pspClosedInjection": True,
        "pspClosedLevel": True,
        "pspClosedWithdrawal": True,
        "pspOpenInjection": True,
        "pspOpenLevel": True,
        "pspOpenWithdrawal": True,
        "renw1": True,
        "renw2": True,
        "renw3": True,
        "renw4": True,
        "resGenerationByPlant": True,
        "rowBal": True,
        "solar": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "spilEnrg": True,
        "stsInjByPlant": True,
        "stsLvlByPlant": True,
        "stsWithdrawalByPlant": True,
        "ucapLin": True,
        "unspEnrg": True,
        "wind": True,
        "windOffshore": True,
        "windOnshore": True,
    }

    client.put(
        f"/v1/studies/{study_id}/config/thematictrimming/form",
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
    res = client.get(f"/v1/studies/{study_id}/config/thematictrimming/form")
    obj = res.json()
    assert obj == {
        "avlDtg": True,
        "balance": True,
        "batteryInjection": True,
        "batteryLevel": True,
        "batteryWithdrawal": True,
        "co2Emis": True,
        "coal": True,
        "congFeeAbs": True,
        "congFeeAlg": True,
        "congProbMinus": True,
        "congProbPlus": True,
        "dens": True,
        "dtgByPlant": True,
        "dtgMrg": True,
        "flowLin": True,
        "flowQuad": True,
        "gas": True,
        "hCost": True,
        "hInfl": True,
        "hLev": True,
        "hOvfl": True,
        "hPump": True,
        "hRor": True,
        "hStor": True,
        "hVal": True,
        "hurdleCost": True,
        "lignite": True,
        "load": True,
        "lold": True,
        "lolp": True,
        "loopFlow": True,
        "margCost": True,
        "maxMrg": True,
        "miscDtg": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "miscNdg": True,
        "mixFuel": True,
        "mrgPrice": True,
        "nodu": True,
        "noduByPlant": True,
        "npCost": True,
        "npCostByPlant": True,
        "nuclear": True,
        "oil": True,
        "opCost": True,
        "other1Injection": True,
        "other1Level": True,
        "other1Withdrawal": True,
        "other2Injection": True,
        "other2Level": True,
        "other2Withdrawal": True,
        "other3Injection": True,
        "other3Level": True,
        "other3Withdrawal": True,
        "other4Injection": True,
        "other4Level": True,
        "other4Withdrawal": True,
        "other5Injection": True,
        "other5Level": True,
        "other5Withdrawal": True,
        "ovCost": True,
        "pondageInjection": True,
        "pondageLevel": True,
        "pondageWithdrawal": True,
        "profitByPlant": True,
        "psp": True,
        "pspClosedInjection": True,
        "pspClosedLevel": True,
        "pspClosedWithdrawal": True,
        "pspOpenInjection": True,
        "pspOpenLevel": True,
        "pspOpenWithdrawal": True,
        "renw1": True,
        "renw2": True,
        "renw3": True,
        "renw4": True,
        "resGenerationByPlant": True,
        "rowBal": True,
        "solar": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "spilEnrg": True,
        "stsInjByPlant": True,
        "stsLvlByPlant": True,
        "stsWithdrawalByPlant": True,
        "ucapLin": True,
        "unspEnrg": True,
        "wind": True,
        "windOffshore": True,
        "windOnshore": True,
    }

    # Properties form

    res_properties_config = client.get(f"/v1/studies/{study_id}/areas/area 1/properties/form")
    res_properties_config_json = res_properties_config.json()
    res_properties_config_json["filterSynthesis"] = set(res_properties_config_json["filterSynthesis"])
    res_properties_config_json["filterByYear"] = set(res_properties_config_json["filterByYear"])
    assert res_properties_config_json == {
        "energyCostUnsupplied": 0.0,
        "energyCostSpilled": 0.0,
        "nonDispatchPower": True,
        "dispatchHydroPower": True,
        "otherDispatchPower": True,
        "filterSynthesis": {"hourly", "daily", "weekly", "monthly", "annual"},
        "filterByYear": {"hourly", "daily", "weekly", "monthly", "annual"},
        "adequacyPatchMode": "outside",
    }

    client.put(
        f"/v1/studies/{study_id}/areas/area 1/properties/form",
        json={
            "energyCostUnsupplied": 2.0,
            "energyCostSpilled": 4.0,
            "nonDispatchPower": False,
            "dispatchHydroPower": False,
            "otherDispatchPower": False,
            "filterSynthesis": ["monthly", "annual"],
            "filterByYear": ["hourly", "daily", "annual"],
            "adequacyPatchMode": "inside",
        },
    )
    res_properties_config = client.get(f"/v1/studies/{study_id}/areas/area 1/properties/form")
    res_properties_config_json = res_properties_config.json()
    res_properties_config_json["filterSynthesis"] = set(res_properties_config_json["filterSynthesis"])
    res_properties_config_json["filterByYear"] = set(res_properties_config_json["filterByYear"])
    assert res_properties_config_json == {
        "energyCostUnsupplied": 2.0,
        "energyCostSpilled": 4.0,
        "nonDispatchPower": False,
        "dispatchHydroPower": False,
        "otherDispatchPower": False,
        "filterSynthesis": {"monthly", "annual"},
        "filterByYear": {"hourly", "daily", "annual"},
        "adequacyPatchMode": "inside",
    }

    # Hydro form

    res_hydro_config = client.put(
        f"/v1/studies/{study_id}/areas/area 1/hydro/form",
        json={
            "interDailyBreakdown": 8,
            "intraDailyModulation": 7,
            "interMonthlyBreakdown": 5,
            "reservoir": True,
        },
    )
    assert res_hydro_config.status_code == 200

    res_hydro_config = client.get(f"/v1/studies/{study_id}/areas/area 1/hydro/form")
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

    res_ts_config = client.get(f"/v1/studies/{study_id}/config/timeseries/form")
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
        json={
            "thermal": {"stochasticTsStatus": True},
            "load": {
                "stochasticTsStatus": True,
                "storeInInput": True,
                "seasonCorrelation": "monthly",
            },
        },
    )
    res_ts_config = client.get(f"/v1/studies/{study_id}/config/timeseries/form")
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

    # Renewable form

    res = client.put(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
        json={
            "name": "cluster renewable 1 renamed",
            "tsInterpretation": "production-factor",
            "unitCount": 9,
            "enabled": False,
            "nominalCapacity": 3,
        },
    )
    assert res.status_code == 200, res.json()

    res = client.get(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
    )
    expected = {
        "enabled": False,
        "group": "Other RES 1",  # Default group used when not specified.
        "id": "cluster renewable 1",
        "name": "cluster renewable 1 renamed",
        "nominalCapacity": 3.0,
        "tsInterpretation": "production-factor",
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
        "costGeneration": "SetManually",
        "efficiency": 100.0,
        "variableOMCost": 0.0,
    }
    res = client.put(
        # This URL is deprecated, but we must check it for backward compatibility.
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
        json=obj,
    )
    assert res.status_code == 200, res.json()

    res = client.get(
        # This URL is deprecated, but we must check it for backward compatibility.
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
    )
    assert res.status_code == 200, res.json()
    assert res.json() == {"id": "cluster 1", **obj}

    # Links

    client.delete(f"/v1/studies/{study_id}/links/area%201/area%202")
    res_links = client.get(f"/v1/studies/{study_id}/links")
    assert res_links.json() == []

    res = client.put(
        f"/v1/studies/{study_id}/areas/area%201/ui",
        json={"x": 100, "y": 100, "color_rgb": [255, 0, 100]},
    )
    res = client.put(
        f"/v1/studies/{study_id}/areas/area%202/ui?layer=1",
        json={"x": 105, "y": 105, "color_rgb": [255, 10, 100]},
    )
    assert res.status_code == 200
    res_ui = client.get(f"/v1/studies/{study_id}/areas?ui=true")
    assert res_ui.json() == {
        "area 1": {
            "ui": {
                "x": 100,
                "y": 100,
                "color_r": 255,
                "color_g": 0,
                "color_b": 100,
                "layers": "0",
            },
            "layerX": {"0": 100},
            "layerY": {"0": 100},
            "layerColor": {"0": "255, 0, 100"},
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
            "layerColor": {"0": "230, 108, 44", "1": "255, 10, 100"},
        },
    }

    # check that at this stage the area cannot be deleted as it is referenced in binding constraint 1
    result = client.delete(f"/v1/studies/{study_id}/areas/area%201")
    assert result.status_code == 403, res.json()
    # verify the error message
    description = result.json()["description"]
    assert all([elm in description for elm in ["area 1", "binding constraint 1"]])
    # check the exception
    assert result.json()["exception"] == "AreaDeletionNotAllowed"

    # delete binding constraint 1
    client.delete(f"/v1/studies/{study_id}/bindingconstraints/binding%20constraint%201")
    # check now that we can delete the area 1
    result = client.delete(f"/v1/studies/{study_id}/areas/area%201")
    assert result.status_code == 200, res.json()
    res_areas = client.get(f"/v1/studies/{study_id}/areas")
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
            "set": ["area 2"],
            "thermals": None,
            "type": "DISTRICT",
        },
    ]


def test_archive(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    study_res = client.post("/v1/studies?name=foo")
    study_id = study_res.json()

    res = client.put(f"/v1/studies/{study_id}/archive")
    assert res.status_code == 200
    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
        ).json()["status"]
        == 3
    )

    res = client.get(f"/v1/studies/{study_id}")
    assert res.json()["archived"]
    assert (tmp_path / "archive_dir" / f"{study_id}.zip").exists()

    res = client.put(f"/v1/studies/{study_id}/unarchive")

    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
        ).json()["status"]
        == 3
    )

    res = client.get(f"/v1/studies/{study_id}")
    assert not res.json()["archived"]
    assert not (tmp_path / "archive_dir" / f"{study_id}.zip").exists()


def test_maintenance(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create non admin user
    res = client.post(
        "/v1/users",
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
        )
        assert result.status_code == 200

        result = client.get(
            "/v1/core/maintenance",
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
        json=message,
    )
    assert res.status_code == 200

    # Set message info when not admin
    res = client.get("/v1/core/maintenance/message")
    assert res.status_code == 200
    assert res.json() == message


def test_import(client: TestClient, admin_access_token: str, study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    zip_path = ASSETS_DIR / "STA-mini.zip"
    seven_zip_path = ASSETS_DIR / "STA-mini.7z"

    # Admin who belongs to a group imports a study
    uuid = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(zip_path.read_bytes())},
    ).json()
    res = client.get(f"v1/studies/{uuid}").json()
    assert res["groups"] == [{"id": "admin", "name": "admin"}]
    assert res["public_mode"] == "NONE"

    # Create user George who belongs to no group
    client.post(
        "/v1/users",
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
    assert res["public_mode"] == "READ"

    # create George group
    george_group = "george_group"
    res = client.post(
        "/v1/groups",
        json={"id": george_group, "name": george_group},
    )
    assert res.status_code in {200, 201}
    # add George to the group as a reader
    client.post(
        "/v1/roles",
        json={"type": 10, "group_id": george_group, "identity_id": 2},
    )
    # reset login to update credentials
    res = client.post(
        "/v1/refresh",
        headers={"Authorization": f'Bearer {george_credentials["refresh_token"]}'},
    )
    george_credentials = res.json()

    # George imports a study, and it should succeed even if he has only "READER" access in the group
    georges_headers = {"Authorization": f'Bearer {george_credentials["access_token"]}'}
    res = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(zip_path.read_bytes())},
        headers=georges_headers,
    )
    assert res.status_code in {200, 201}
    uuid = res.json()
    res = client.get(f"v1/studies/{uuid}", headers=georges_headers).json()
    assert res["groups"] == [{"id": george_group, "name": george_group}]
    assert res["public_mode"] == "NONE"

    # Study importer works for 7z files
    res = client.post(
        "/v1/studies/_import",
        files={"study": io.BytesIO(seven_zip_path.read_bytes())},
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
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Copy a study with admin user who belongs to a group
    copied = client.post(f"/v1/studies/{study_id}/copy?dest=copied&use_task=false")
    assert copied.status_code == 201
    # asserts that it has admin groups and PublicMode to NONE
    res = client.get(f"/v1/studies/{copied.json()}").json()
    assert res["groups"] == [{"id": "admin", "name": "admin"}]
    assert res["public_mode"] == "NONE"

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
    res = client.get(f"/v1/studies/{copied.json()}").json()
    assert res["groups"] == []
    assert res["public_mode"] == "READ"


def test_links_deletion(client: TestClient, user_access_token: str, study_id: str) -> None:
    """
    Test the deletion of links between areas.
    """

    # set client headers to user access token
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create an area "area_1" in the study
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={
            "name": "area_1",
            "type": "AREA",
            "metadata": {"country": "FR"},
        },
    )
    assert res.status_code == 200, res.json()

    # Create an area "area_2" in the study
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={
            "name": "area_2",
            "type": "AREA",
            "metadata": {"country": "DE"},
        },
    )
    assert res.status_code == 200, res.json()

    # create a link between the two areas
    res = client.post(
        f"/v1/studies/{study_id}/links",
        json={
            "area1": "area_1",
            "area2": "area_2",
        },
    )
    assert res.status_code == 200, res.json()

    # create a binding constraint that references the link
    bc_obj = {
        "name": "bc_1",
        "enabled": True,
        "time_step": "hourly",
        "operator": "less",
        "terms": [
            {
                "id": "area_1%area_2",
                "weight": 2,
                "data": {"area1": "area_1", "area2": "area_2"},
            }
        ],
    }
    res = client.post(
        f"/v1/studies/{study_id}/bindingconstraints",
        json=bc_obj,
    )
    assert res.status_code == 200, res.json()

    # try to delete the link before deleting the binding constraint
    res = client.delete(f"/v1/studies/{study_id}/links/area_1/area_2")
    assert res.status_code == 403, res.json()
    description = res.json()["description"]
    assert all([elm in description for elm in ["area_1%area_2", "bc_1"]])
    assert res.json()["exception"] == "LinkDeletionNotAllowed"

    # delete the binding constraint
    res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/bc_1")
    assert res.status_code == 200, res.json()

    # delete the link
    res = client.delete(f"/v1/studies/{study_id}/links/area_1/area_2")
    assert res.status_code == 200, res.json()
