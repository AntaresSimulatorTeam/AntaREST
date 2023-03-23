import contextlib
import time
from pathlib import Path
from typing import Callable
from unittest.mock import ANY

from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.study.business.adequacy_patch_management import PriceTakingOrder
from antarest.study.business.area_management import AreaType, LayerInfoDTO
from antarest.study.business.general_management import Mode
from antarest.study.business.optimization_management import (
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
    SimplexOptimizationRange,
)
from antarest.study.business.table_mode_management import (
    FIELDS_INFO_BY_TYPE,
    AdequacyPatchMode,
    AssetType,
    LawOption,
    TableTemplateType,
    TimeSeriesGenerationOption,
    TransmissionCapacity,
    TimeSeriesInterpretation,
    BindingConstraintType,
    BindingConstraintOperator,
)
from antarest.study.model import MatrixIndex, StudyDownloadLevelDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from fastapi import FastAPI
from starlette.testclient import TestClient


def wait_for(predicate: Callable[[], bool], timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        with contextlib.suppress(Exception):
            if predicate():
                return
        time.sleep(1)
    raise TimeoutError()


def init_test(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)

    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    # check default study presence
    study_count = 0
    countdown = 10
    while study_count == 0 or countdown > 0:
        res = client.get(
            "/v1/studies",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        )
        time.sleep(1)
        studies_info = res.json()
        study_count = len(studies_info)
        countdown -= 1

    return client, admin_credentials


def test_main(app: FastAPI):
    client, admin_credentials = init_test(app)

    # create some new users
    # TODO check for bad username or empty password
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Harry", "password": "mypass"},
    )
    res = client.get(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 4

    # reject user with existing name creation
    res = client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "George", "password": "mypass"},
    )
    assert res.status_code == 400

    # login with new user
    # TODO mock ldap connector and test user login
    res = client.post(
        "/v1/login", json={"username": "George", "password": "mypass"}
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/login", json={"username": "Fred", "password": "mypass"}
    )
    fred_credentials = res.json()
    res = client.post(
        "/v1/login", json={"username": "Harry", "password": "mypass"}
    )
    harry_credentials = res.json()

    # reject user creation from non admin
    res = client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json={"name": "Fred", "password": "mypass"},
    )
    assert res.status_code == 403

    # check study listing
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1
    study_id = next(iter(res.json()))
    comments = "<text>Hello</text>"

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res_output = res.json()
    assert len(res_output) == 5

    res = client.get(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco/variables",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 417
    assert res.json()["description"] == "Not a year by year simulation"

    # Set new comments
    res = client.put(
        f"/v1/studies/{study_id}/comments",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json={"comments": comments},
    )

    # Get comments
    res = client.get(
        f"/v1/studies/{study_id}/comments",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.json() == comments

    # study synthesis
    res = client.get(
        f"/v1/studies/{study_id}/synthesis",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # playlist
    res = client.post(
        f"/v1/studies/{study_id}/raw?path=settings/generaldata/general/nbyears",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json=5,
    )
    assert res.status_code == 204

    res = client.put(
        f"/v1/studies/{study_id}/config/playlist",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
        json={"playlist": [1, 2], "weights": {1: 8.0, 3: 9.0}},
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/config/playlist",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert res.json() == {"1": 8.0, "2": 1.0}

    # scenario builder
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
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
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
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
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # study matrix index
    res = client.get(
        f"/v1/studies/{study_id}/matrixindex",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert (
        res.json()
        == MatrixIndex(
            first_week_size=7,
            start_date="2001-01-01 00:00:00",
            steps=8760,
            level=StudyDownloadLevelDTO.HOURLY,
        ).dict()
    )

    res = client.get(
        f"/v1/studies/{study_id}/matrixindex?path=output/20201014-1427eco/economy/mc-all/areas/es/details-daily",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert (
        res.json()
        == MatrixIndex(
            first_week_size=7,
            start_date="2001-01-01 00:00:00",
            steps=7,
            level=StudyDownloadLevelDTO.DAILY,
        ).dict()
    )

    res = client.delete(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 4

    # study creation
    created = client.post(
        "/v1/studies?name=foo",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert created.status_code == 201

    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # Study copy
    copied = client.post(
        f"/v1/studies/{created.json()}/copy?dest=copied&use_task=false",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert copied.status_code == 201

    updated = client.put(
        f"/v1/studies/{copied.json()}/move?folder_dest=foo/bar",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert updated.status_code == 200

    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 3
    assert (
        filter(
            lambda s: s["id"] == copied.json(), res.json().values()
        ).__next__()["folder"]
        == "foo/bar"
    )

    res = client.post(
        "/v1/studies/_invalidate_cache_listing",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Study delete
    client.delete(
        f"/v1/studies/{copied.json()}",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )

    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # check study permission
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1

    # play with groups
    res = client.post(
        "/v1/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "Weasley"},
    )
    res = client.get(
        "/v1/groups",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    group_id = res.json()[1]["id"]
    res = client.post(
        "/v1/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 40, "group_id": group_id, "identity_id": 3},
    )
    res = client.post(
        "/v1/roles",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"type": 30, "group_id": group_id, "identity_id": 2},
    )
    # reset login to update credentials
    res = client.post(
        "/v1/refresh",
        headers={
            "Authorization": f'Bearer {george_credentials["refresh_token"]}'
        },
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/refresh",
        headers={
            "Authorization": f'Bearer {fred_credentials["refresh_token"]}'
        },
    )
    fred_credentials = res.json()
    res = client.post(
        f"/v1/studies?name=bar&groups={group_id}",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {george_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 3
    res = client.get(
        "/v1/studies",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2

    # running studies
    # TODO use a local launcher mock instead of using a local launcher with launcher_mock.sh (doesn't work..)
    studies = [
        study_id
        for study_id in res.json()
        if res.json()[study_id]["name"] == "STA-mini"
    ]
    study_id = studies[0]
    res = client.post(
        f"/v1/launcher/run/{study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    job_id = res.json()["job_id"]
    res = client.get(
        f"/v1/launcher/jobs?study_id={study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert res.json()[0]["id"] == job_id

    # update metadata
    res = client.put(
        f"/v1/studies/{study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
        json={
            "name": "STA-mini-copy",
            "status": "copied",
            "horizon": "2035",
            "author": "Luffy",
        },
    )
    new_meta = client.get(
        f"/v1/studies/{study_id}",
        headers={
            "Authorization": f'Bearer {fred_credentials["access_token"]}'
        },
    )
    assert res.json() == new_meta.json()
    assert new_meta.json()["status"] == "copied"
    assert new_meta.json()["name"] == "STA-mini-copy"
    assert new_meta.json()["horizon"] == "2035"


def test_matrix(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    matrix = [[1, 2], [3, 4]]

    res = client.post(
        "/v1/matrix",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=matrix,
    )

    assert res.status_code == 200

    res = client.get(
        f"/v1/matrix/{res.json()}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )

    assert res.status_code == 200
    stored = res.json()
    assert stored["created_at"] > 0
    assert stored["id"] != ""

    matrix_id = stored["id"]

    res = client.get(
        f"/v1/matrix/{matrix_id}/download",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        "/v1/matrixdataset/_search?name=myda",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    results = res.json()
    assert len(results) == 1
    assert len(results[0]["matrices"]) == 1
    assert results[0]["matrices"][0]["id"] == matrix_id

    dataset_id = results[0]["id"]
    res = client.get(
        f"/v1/matrixdataset/{dataset_id}/download",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.delete(
        f"/v1/matrixdataset/{dataset_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200


def test_area_management(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    created = client.post(
        "/v1/studies?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    study_id = created.json()
    res_areas = client.get(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "name": "area 1",
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR", "tags": ["a"]},
        },
    )
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "name": "area 2",
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=[
            {
                "action": CommandName.CREATE_CLUSTER.value,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=[
            {
                "action": CommandName.CREATE_CLUSTER.value,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 1",
                    "enabled": True,
                    "time_step": BindingConstraintType.HOURLY.value,
                    "operator": BindingConstraintOperator.LESS.value,
                    "coeffs": {"area 1.cluster 1": [2.0, 4]},
                },
            }
        ],
    )

    client.post(
        f"/v1/studies/{study_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=[
            {
                "action": CommandName.CREATE_BINDING_CONSTRAINT.value,
                "args": {
                    "name": "binding constraint 2",
                    "enabled": True,
                    "time_step": BindingConstraintType.HOURLY.value,
                    "operator": BindingConstraintOperator.LESS.value,
                    "coeffs": {},
                },
            }
        ],
    )

    res_areas = client.get(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "area1": "area 1",
            "area2": "area 2",
        },
    )
    res_links = client.get(
        f"/v1/studies/{study_id}/links?with_ui=true",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_links.json() == [
        {
            "area1": "area 1",
            "area2": "area 2",
            "ui": {"color": "112,112,112", "style": "plain", "width": 1.0},
        }
    ]

    # -- `layers` integration tests

    res = client.get(
        f"/v1/studies/{study_id}/layers",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict()
    ]

    res = client.post(
        f"/v1/studies/{study_id}/layers?name=test",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json() == "1"

    res = client.get(
        f"/v1/studies/{study_id}/layers",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test", areas=[]).dict(),
    ]

    res = client.put(
        f"/v1/studies/{study_id}/layers/1?name=test2",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res = client.put(
        f"/v1/studies/{study_id}/layers/1",
        json=["area 1"],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res = client.put(
        f"/v1/studies/{study_id}/layers/1",
        json=["area 2"],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res = client.get(
        f"/v1/studies/{study_id}/layers",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).dict(),
        LayerInfoDTO(id="1", name="test2", areas=["area 2"]).dict(),
    ]

    # -- `district` integration tests

    res = client.post(
        f"/v1/studies/{study_id}/districts",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "name": "District 1",
            "output": True,
            "comments": "Your District",
            "areas": [],
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/districts",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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

    res = client.delete(
        f"/v1/studies/{study_id}/districts/district%201",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Optimization form

    res_optimization_config = client.get(
        f"/v1/studies/{study_id}/config/optimization/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "strategicReserve": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
            "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
        },
    )
    res_optimization_config = client.get(
        f"/v1/studies/{study_id}/config/optimization/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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

    res_adequacy_patch_config = client.get(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
            "priceTakingOrder": PriceTakingOrder.LOAD.value,
            "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        },
    )
    res_adequacy_patch_config = client.get(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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

    res_general_config = client.get(
        f"/v1/studies/{study_id}/config/general/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "mode": Mode.ADEQUACY.value,
            "lastDay": 299,
            "leapYear": True,
        },
    )
    res_general_config = client.get(
        f"/v1/studies/{study_id}/config/general/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res_general_config_json = res_general_config.json()
    assert res_general_config_json == {
        "mode": Mode.ADEQUACY.value,
        "firstDay": 1,
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
        f"/v1/studies/{study_id}/config/thematictrimming/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
        "congProdPlus": True,
        "congProdMinus": True,
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
        "profit": True,
    }

    client.put(
        f"/v1/studies/{study_id}/config/thematictrimming/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
            "congProdPlus": True,
            "congProdMinus": True,
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
            "profit": True,
        },
    )
    res_thematic_trimming_config = client.get(
        f"/v1/studies/{study_id}/config/thematictrimming/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
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
        "congProdPlus": True,
        "congProdMinus": True,
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
        "profit": True,
    }

    # Hydro form

    res_hydro_config = client.put(
        f"/v1/studies/{study_id}/areas/area1/hydro/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "interDailyBreakdown": 8,
            "intraDailyModulation": 7,
            "interMonthlyBreakdown": 5,
            "reservoir": True,
        },
    )
    assert res_hydro_config.status_code == 200

    res_hydro_config = client.get(
        f"/v1/studies/{study_id}/areas/area1/hydro/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        "leewayLow": 1,
        "leewayUp": 1,
        "pumpingEfficiency": 1,
    }

    # Time-series form

    res_ts_config = client.get(
        f"/v1/studies/{study_id}/config/timeseries/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "thermal": {"stochasticTsStatus": True},
            "load": {
                "stochasticTsStatus": True,
                "storeInInput": True,
                "seasonCorrelation": "monthly",
            },
        },
    )
    res_ts_config = client.get(
        f"/v1/studies/{study_id}/config/timeseries/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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

    table_mode_url = f"/v1/studies/{study_id}/tablemode/form"

    # Table Mode - Area

    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.AREA,
            "columns": ",".join(FIELDS_INFO_BY_TYPE[TableTemplateType.AREA]),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1": {
            "nonDispatchablePower": True,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "spreadUnsuppliedEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 0.0,
            "averageUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "adequacyPatchMode": "outside",
        },
        "area 2": {
            "nonDispatchablePower": True,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "spreadUnsuppliedEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 0.0,
            "averageUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "adequacyPatchMode": "outside",
        },
    }

    client.put(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.AREA,
        },
        json={
            "area 1": {
                "nonDispatchablePower": False,
                "spreadSpilledEnergyCost": 1.1,
                "filterYearByYear": "monthly, annual",
            },
            "area 2": {
                "nonDispatchablePower": True,
                "spreadSpilledEnergyCost": 3.0,
                "filterSynthesis": "hourly",
                "adequacyPatchMode": AdequacyPatchMode.INSIDE.value,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.AREA,
            "columns": ",".join(
                list(FIELDS_INFO_BY_TYPE[TableTemplateType.AREA])
            ),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "area 1": {
            "nonDispatchablePower": False,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "spreadUnsuppliedEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 1.1,
            "averageUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "monthly, annual",
            "adequacyPatchMode": "outside",
        },
        "area 2": {
            "nonDispatchablePower": True,
            "dispatchableHydroPower": True,
            "otherDispatchablePower": True,
            "spreadUnsuppliedEnergyCost": 0.0,
            "spreadSpilledEnergyCost": 3.0,
            "averageUnsuppliedEnergyCost": 0.0,
            "averageSpilledEnergyCost": 0.0,
            "filterSynthesis": "hourly",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "adequacyPatchMode": "outside",
        },
    }

    # Table Mode - Link

    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.LINK,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.LINK,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.LINK,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.CLUSTER,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.CLUSTER]
            ),
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
            "tsGen": "use global parameter",
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
            "tsGen": "use global parameter",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
        },
    }

    client.put(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.CLUSTER,
        },
        json={
            "area 1 / cluster 1": {
                "enabled": False,
                "unitCount": 3,
                "spinning": 8,
                "tsGen": TimeSeriesGenerationOption.FORCE_GENERATION.value,
                "lawPlanned": LawOption.GEOMETRIC.value,
            },
            "area 2 / cluster 2": {
                "nominalCapacity": 2,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.CLUSTER,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.CLUSTER]
            ),
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
            "tsGen": "use global parameter",
            "volatilityForced": 0,
            "volatilityPlanned": 0,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
        },
    }

    # Table Mode - Renewable

    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.RENEWABLE,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.RENEWABLE]
            ),
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.RENEWABLE,
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.RENEWABLE,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.RENEWABLE]
            ),
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
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.BINDING_CONSTRAINT]
            ),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "binding constraint 1": {
            "enabled": True,
            "type": BindingConstraintType.HOURLY.value,
            "operator": BindingConstraintOperator.LESS.value,
        },
        "binding constraint 2": {
            "enabled": True,
            "type": BindingConstraintType.HOURLY.value,
            "operator": BindingConstraintOperator.LESS.value,
        },
    }

    client.put(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT,
        },
        json={
            "binding constraint 1": {
                "enabled": False,
                "operator": BindingConstraintOperator.BOTH.value,
            },
            "binding constraint 2": {
                "type": BindingConstraintType.WEEKLY.value,
                "operator": BindingConstraintOperator.EQUAL.value,
            },
        },
    )
    res_table_data = client.get(
        table_mode_url,
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        params={
            "table_type": TableTemplateType.BINDING_CONSTRAINT,
            "columns": ",".join(
                FIELDS_INFO_BY_TYPE[TableTemplateType.BINDING_CONSTRAINT]
            ),
        },
    )
    res_table_data_json = res_table_data.json()
    assert res_table_data_json == {
        "binding constraint 1": {
            "enabled": False,
            "type": BindingConstraintType.HOURLY.value,
            "operator": BindingConstraintOperator.BOTH.value,
        },
        "binding constraint 2": {
            "enabled": True,
            "type": BindingConstraintType.WEEKLY.value,
            "operator": BindingConstraintOperator.EQUAL.value,
        },
    }

    res = client.get(
        f"/v1/studies/{study_id}/bindingconstraints/binding constraint 1",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraint_1 = res.json()
    assert res.status_code == 200

    constraint = binding_constraint_1["constraints"][0]
    assert constraint["id"] == "area 1.cluster 1"
    assert constraint["weight"] == 2.0
    assert constraint["offset"] == 4.0

    # --- TableMode END ---

    # Renewable form

    res_renewable_config = client.put(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "name": "cluster renewable 1 renamed",
            "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR.value,
            "unitCount": 9,
            "enabled": False,
            "nominalCapacity": 3,
        },
    )
    assert res_renewable_config.status_code == 200

    res_renewable_config = client.get(
        f"/v1/studies/{study_id}/areas/area 1/clusters/renewable/cluster renewable 1/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res_renewable_config_json = res_renewable_config.json()

    assert res_renewable_config_json == {
        "group": "",
        "tsInterpretation": TimeSeriesInterpretation.PRODUCTION_FACTOR.value,
        "name": "cluster renewable 1 renamed",
        "unitCount": 9,
        "enabled": False,
        "nominalCapacity": 3,
    }

    # Thermal form

    res_thermal_config = client.put(
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={
            "group": "Lignite",
            "name": "cluster 1 renamed",
            "unitCount": 3,
            "enabled": False,
            "nominalCapacity": 3,
            "genTs": "use global parameter",
            "minStablePower": 3,
            "minUpTime": 3,
            "minDownTime": 3,
            "mustRun": False,
            "spinning": 3,
            "co2": 3,
            "volatilityForced": 3,
            "volatilityPlanned": 3,
            "lawForced": "uniform",
            "lawPlanned": "uniform",
            "marginalCost": 3,
            "spreadCost": 3,
            "fixedCost": 3,
            "startupCost": 3,
            "marketBidCost": 3,
        },
    )
    assert res_thermal_config.status_code == 200

    res_thermal_config = client.get(
        f"/v1/studies/{study_id}/areas/area 1/clusters/thermal/cluster 1/form",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res_thermal_config_json = res_thermal_config.json()

    assert res_thermal_config_json == {
        "group": "Lignite",
        "name": "cluster 1 renamed",
        "unitCount": 3,
        "enabled": False,
        "nominalCapacity": 3,
        "genTs": TimeSeriesGenerationOption.USE_GLOBAL_PARAMETER.value,
        "minStablePower": 3,
        "minUpTime": 3,
        "minDownTime": 3,
        "mustRun": False,
        "spinning": 3,
        "co2": 3,
        "volatilityForced": 3,
        "volatilityPlanned": 3,
        "lawForced": LawOption.UNIFORM.value,
        "lawPlanned": LawOption.UNIFORM.value,
        "marginalCost": 3,
        "spreadCost": 3,
        "fixedCost": 3,
        "startupCost": 3,
        "marketBidCost": 3,
    }

    # Links

    client.delete(
        f"/v1/studies/{study_id}/links/area%201/area%202",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res_links = client.get(
        f"/v1/studies/{study_id}/links",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_links.json() == []

    res = client.put(
        f"/v1/studies/{study_id}/areas/area%201/ui",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"x": 100, "y": 100, "color_rgb": [255, 0, 100]},
    )
    res = client.put(
        f"/v1/studies/{study_id}/areas/area%202/ui?layer=1",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"x": 105, "y": 105, "color_rgb": [255, 10, 100]},
    )
    assert res.status_code == 200
    res_ui = client.get(
        f"/v1/studies/{study_id}/areas?ui=true",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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

    result = client.delete(
        f"/v1/studies/{study_id}/areas/area%201",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert result.status_code == 200
    res_areas = client.get(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
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


def test_archive(app: FastAPI, tmp_path: Path):
    client, admin_credentials = init_test(app)

    study_res = client.post(
        "/v1/studies?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    study_id = study_res.json()

    res = client.put(
        f"/v1/studies/{study_id}/archive",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        ).json()["status"]
        == 3
    )

    res = client.get(
        f"/v1/studies/{study_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json()["archived"]
    assert (tmp_path / "archive_dir" / f"{study_id}.zip").exists()

    res = client.put(
        f"/v1/studies/{study_id}/unarchive",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )

    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        ).json()["status"]
        == 3
    )

    res = client.get(
        f"/v1/studies/{study_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert not res.json()["archived"]
    assert not (tmp_path / "archive_dir" / f"{study_id}.zip").exists()


def test_variant_manager(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)

    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    base_study_res = client.post(
        "/v1/studies?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )

    base_study_id = base_study_res.json()

    res = client.post(
        f"/v1/studies/{base_study_id}/variants?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    variant_id = res.json()
    client.post(
        f"/v1/studies/{variant_id}/variants?name=bar",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    client.post(
        f"/v1/studies/{variant_id}/variants?name=baz",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res = client.get(
        f"/v1/studies/{base_study_id}/variants",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    children = res.json()
    assert children["node"]["name"] == "foo"
    assert len(children["children"]) == 1
    assert children["children"][0]["node"]["name"] == "foo"
    assert len(children["children"][0]["children"]) == 2
    assert children["children"][0]["children"][0]["node"]["name"] == "bar"
    assert children["children"][0]["children"][1]["node"]["name"] == "baz"

    res = client.post(
        f"/v1/studies/{base_study_id}/variants?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    variant_id = res.json()
    res = client.get(
        f"/v1/studies/{variant_id}/parents",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == base_study_id
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{variant_id}/commands",
        json=[
            {
                "action": "create_area",
                "args": {"area_name": "testZone", "metadata": {}},
            }
        ],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.post(
        f"/v1/studies/{variant_id}/commands",
        json=[
            {
                "action": "create_area",
                "args": {"area_name": "testZone2", "metadata": {}},
            }
        ],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{variant_id}/command",
        json={
            "action": "create_area",
            "args": {"area_name": "testZone3", "metadata": {}},
        },
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    command_id = res.json()
    res = client.put(
        f"/v1/studies/{variant_id}/commands/{command_id}",
        json={
            "action": "create_area",
            "args": {"area_name": "testZone4", "metadata": {}},
        },
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{variant_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 3
    assert res.status_code == 200

    res = client.put(
        f"/v1/studies/{variant_id}/commands",
        json=[
            {
                "action": "create_area",
                "args": {"area_name": "testZoneReplace1", "metadata": {}},
            },
            {
                "action": "create_area",
                "args": {"area_name": "testZoneReplace1", "metadata": {}},
            },
        ],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{variant_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 2
    assert res.status_code == 200

    command_id = res.json()[1]["id"]

    res = client.put(
        f"/v1/studies/{variant_id}/commands/{command_id}/move?index=0",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{variant_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.json()[0]["id"] == command_id
    assert res.status_code == 200

    res = client.delete(
        f"/v1/studies/{variant_id}/commands/{command_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )

    assert res.status_code == 200

    res = client.put(
        f"/v1/studies/{variant_id}/generate",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/tasks/{res.json()}?wait_for_completion=true",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    task_result = TaskDTO.parse_obj(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result.success

    res = client.get(
        f"/v1/studies/{variant_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{variant_id}/freeze?name=bar",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 500

    new_study_id = "newid"

    res = client.get(
        f"/v1/studies/{new_study_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 404

    res = client.delete(
        f"/v1/studies/{variant_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{variant_id}/commands",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert len(res.json()) == 0

    res = client.delete(
        f"/v1/studies/{variant_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{variant_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 404


def test_maintenance(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)

    # Get admin credentials
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    # Create non admin user
    res = client.post(
        "/v1/users",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "user", "password": "user"},
    )
    assert res.status_code == 200

    res = client.post(
        "/v1/login", json={"username": "user", "password": "user"}
    )
    non_admin_credentials = res.json()

    # Test maintenance update utils function
    def set_maintenance(value: bool) -> None:
        # Set maintenance mode
        result = client.post(
            f"/v1/core/maintenance?maintenance={'true' if value else 'false'}",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        )
        assert result.status_code == 200

        result = client.get(
            "/v1/core/maintenance",
            headers={
                "Authorization": f'Bearer {admin_credentials["access_token"]}'
            },
        )
        assert result.status_code == 200
        assert result.json() == value

    set_maintenance(True)
    set_maintenance(False)

    # Set maintenance mode when not admin
    res = client.post(
        "/v1/core/maintenance?maintenance=true",
        headers={
            "Authorization": f'Bearer {non_admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 403

    # Set message info
    message = "Hey"
    res = client.post(
        "/v1/core/maintenance/message",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json=message,
    )
    assert res.status_code == 200

    # Set message info when not admin
    res = client.get(
        "/v1/core/maintenance/message",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200
    assert res.json() == message


def test_edit_matrix(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    headers = {"Authorization": f'Bearer {admin_credentials["access_token"]}'}

    created = client.post(
        "/v1/studies?name=foo",
        headers=headers,
    )
    study_id = created.json()

    area1_name = "area1"
    area2_name = "area2"
    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area1_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR"},
        },
    )
    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area2_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )

    client.post(
        f"/v1/studies/{study_id}/links",
        headers=headers,
        json={
            "area1": area1_name,
            "area2": area2_name,
        },
    )

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    assert res.status_code == 200
    initial_data = res.json()["data"]

    # only one cell
    res = client.put(
        f"/v1/studies/{study_id}/matrix?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
        json=[
            {
                "slices": [{"row_from": 0, "column_from": 0}],
                "operation": {
                    "operation": "+",
                    "value": 1,
                },
            }
        ],
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    new_data = res.json()["data"]
    assert new_data != initial_data
    assert new_data[0][0] == 1

    res = client.put(
        f"/v1/studies/{study_id}/matrix?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
        json=[
            {
                "slices": [{"row_from": 0, "column_from": 0, "column_to": 6}],
                "operation": {
                    "operation": "=",
                    "value": 1,
                },
            }
        ],
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    new_data = res.json()["data"]
    assert new_data != initial_data
    assert new_data[0] == [1] * 6

    res = client.put(
        f"/v1/studies/{study_id}/matrix?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
        json=[
            {
                "coordinates": [(4, 5)],
                "operation": {
                    "operation": "=",
                    "value": 42,
                },
            }
        ],
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    new_data = res.json()["data"]
    assert new_data != initial_data
    assert new_data[4][5] == 42

    res = client.put(
        f"/v1/studies/{study_id}/matrix?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
        json=[
            {
                "slices": [{"row_from": 0, "row_to": 8760, "column_from": 0}],
                "operation": {
                    "operation": "=",
                    "value": 1,
                },
            }
        ],
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    new_data = res.json()["data"]
    assert new_data != initial_data
    assert [a[0] for a in new_data] == [1] * 8760

    res = client.put(
        f"/v1/studies/{study_id}/matrix?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
        json=[
            {
                "slices": [
                    {
                        "row_from": 2,
                        "row_to": 4,
                        "column_from": 2,
                        "column_to": 4,
                    },
                    {
                        "row_from": 9,
                        "row_to": 15,
                        "column_from": 1,
                        "column_to": 3,
                    },
                ],
                "operation": {
                    "operation": "=",
                    "value": 42,
                },
            }
        ],
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/raw?path=input/links/{area1_name}/{area2_name}_parameters",
        headers=headers,
    )
    new_data = res.json()["data"]
    assert new_data != initial_data
    assert [[a[i] for a in new_data[2:4]] for i in range(2, 4)] == [
        [42] * 2
    ] * 2
    assert [[a[i] for a in new_data[9:15]] for i in range(1, 3)] == [
        [42] * 6
    ] * 2


def test_binding_constraint_manager(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    headers = {"Authorization": f'Bearer {admin_credentials["access_token"]}'}

    created = client.post(
        "/v1/studies?name=foo",
        headers=headers,
    )
    study_id = created.json()

    area1_name = "area1"
    area2_name = "area2"
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area1_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR"},
        },
    )
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area2_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{study_id}/links",
        headers=headers,
        json={
            "area1": area1_name,
            "area2": area2_name,
        },
    )
    assert res.status_code == 200

    # Create Variant
    res = client.post(
        f"/v1/studies/{study_id}/variants?name=foo",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    variant_id = res.json()

    # Create Binding constraints
    res = client.post(
        f"/v1/studies/{variant_id}/commands",
        json=[
            {
                "action": "create_binding_constraint",
                "args": {
                    "name": "binding_constraint_1",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "less",
                    "coeffs": {},
                    "comments": "",
                },
            }
        ],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    res = client.post(
        f"/v1/studies/{variant_id}/commands",
        json=[
            {
                "action": "create_binding_constraint",
                "args": {
                    "name": "binding_constraint_2",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "less",
                    "coeffs": {},
                    "comments": "",
                },
            }
        ],
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Get Binding Constraint list
    res = client.get(
        f"/v1/studies/{variant_id}/bindingconstraints",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraints_list = res.json()
    assert res.status_code == 200
    assert len(binding_constraints_list) == 2
    assert binding_constraints_list[0]["id"] == "binding_constraint_1"
    assert binding_constraints_list[1]["id"] == "binding_constraint_2"

    binding_constraint_id = binding_constraints_list[0]["id"]

    # Update element of Binding constraint
    new_comment = "We made it !"
    res = client.put(
        f"v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}",
        json={"key": "comments", "value": new_comment},
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Get Binding Constraint
    res = client.get(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraint = res.json()
    comments = binding_constraint["comments"]
    assert res.status_code == 200
    assert comments == new_comment

    # Add Constraint term
    res = client.post(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}/term",
        json={
            "weight": 1,
            "offset": 2,
            "data": {"area1": area1_name, "area2": area2_name},
        },
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Get Binding Constraint
    res = client.get(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraint = res.json()
    constraints = binding_constraint["constraints"]
    assert res.status_code == 200
    assert binding_constraint["id"] == binding_constraint_id
    assert len(constraints) == 1
    assert constraints[0]["id"] == f"{area1_name}%{area2_name}"
    assert constraints[0]["weight"] == 1
    assert constraints[0]["offset"] == 2
    assert constraints[0]["data"]["area1"] == area1_name
    assert constraints[0]["data"]["area2"] == area2_name

    # Update Constraint term
    res = client.put(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}/term",
        json={
            "id": f"{area1_name}%{area2_name}",
            "weight": 3,
        },
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Get Binding Constraint
    res = client.get(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraint = res.json()
    constraints = binding_constraint["constraints"]
    assert res.status_code == 200
    assert binding_constraint["id"] == binding_constraint_id
    assert len(constraints) == 1
    assert constraints[0]["id"] == f"{area1_name}%{area2_name}"
    assert constraints[0]["weight"] == 3
    assert constraints[0]["offset"] is None
    assert constraints[0]["data"]["area1"] == area1_name
    assert constraints[0]["data"]["area2"] == area2_name

    # Remove Constraint term
    res = client.delete(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}/term/{area1_name}%{area2_name}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 200

    # Get Binding Constraint
    res = client.get(
        f"/v1/studies/{variant_id}/bindingconstraints/{binding_constraint_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    binding_constraint = res.json()
    constraints = binding_constraint["constraints"]
    assert res.status_code == 200
    assert constraints is None
