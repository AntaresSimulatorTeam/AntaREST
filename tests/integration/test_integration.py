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
import os
import zipfile
from http import HTTPStatus
from pathlib import Path
from unittest.mock import ANY

from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp
from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.study.business.area_management import LayerInfoDTO
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
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        json={"name": "Fred", "password": "mypass"},
    )
    assert res.status_code == 403

    # check study listing
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 1
    study_id = next(iter(res.json()))

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    res_output = res.json()
    assert len(res_output) == 6

    res = client.get(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco/variables",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert res.status_code == 417
    assert res.json()["description"] == "Not a year by year simulation"

    # study synthesis
    res = client.get(
        f"/v1/studies/{study_id}/synthesis",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert res.status_code == 200, res.json()

    # Update the active ruleset
    active_ruleset_name = "ruleset test"
    res = client.post(
        f"/v1/studies/{study_id}/raw?path=settings/generaldata/general/active-rules-scenario",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        json=active_ruleset_name.title(),  # ruleset names are case-insensitive
    )
    assert res.status_code == 200

    # scenario builder
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
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
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
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
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert res.status_code == 200

    res = client.delete(
        f"/v1/studies/{study_id}/outputs/20201014-1427eco",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{study_id}/outputs",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 5

    # study creation
    created = client.post(
        "/v1/studies?name=foo",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert created.status_code == 201

    res = client.get(
        f"/v1/studies/{created.json()}/raw?path=study&depth=3&formatted=true",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert res.json()["antares"]["author"] == "George"

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 2

    # Study copy
    copied = client.post(
        f"/v1/studies/{created.json()}/copy?study_name=copied&use_task=false",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert copied.status_code == 201

    updated = client.put(
        f"/v1/studies/{copied.json()}/move?folder_dest=foo/bar",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert updated.status_code == 200

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 3
    moved_study = filter(lambda s: s["id"] == copied.json(), res.json().values()).__next__()
    assert moved_study["folder"] == f"foo/bar/{moved_study['id']}"

    # Study delete
    client.delete(
        f"/v1/studies/{copied.json()}",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )

    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 2

    # check study permission
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
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
        headers={"Authorization": f"Bearer {george_credentials['refresh_token']}"},
    )
    george_credentials = res.json()
    res = client.post(
        "/v1/refresh",
        headers={"Authorization": f"Bearer {fred_credentials['refresh_token']}"},
    )
    fred_credentials = res.json()
    client.post(
        f"/v1/studies?name=bar&groups={group_id}",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 3
    res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
    )
    assert len(res.json()) == 2

    # running studies
    # TODO use a local launcher mock instead of using a local launcher with launcher_mock.sh (doesn't work..)
    studies = [study_id for study_id in res.json() if res.json()[study_id]["name"] == "STA-mini"]
    study_id = studies[0]
    res = client.post(
        f"/v1/launcher/run/{study_id}",
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
    )
    job_id = res.json()["job_id"]

    res = client.get("/v1/launcher/load?launcher_id=local_id")
    assert res.status_code == 200, res.json()
    launcher_load = res.json()
    assert launcher_load["allocatedCpuRate"] == 100 / (os.cpu_count() or 1)
    assert launcher_load["clusterLoadRate"] == 100 / (os.cpu_count() or 1)
    assert launcher_load["nbQueuedJobs"] == 0
    assert launcher_load["launcherStatus"] == "SUCCESS"

    res = client.get(
        f"/v1/launcher/jobs?study_id={study_id}",
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
    )
    job_info = res.json()[0]
    assert job_info == {
        "id": job_id,
        "study_id": study_id,
        "launcher": "local_id",
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
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
        json={
            "name": "STA-mini-copy",
            "horizon": "2035",
            "author": "Luffy",
        },
    )
    new_meta = client.get(
        f"/v1/studies/{study_id}",
        headers={"Authorization": f"Bearer {fred_credentials['access_token']}"},
    )
    assert res.json() == new_meta.json()
    assert new_meta.json()["name"] == "STA-mini-copy"
    assert new_meta.json()["horizon"] == "2035"
    assert new_meta.json()["owner"]["name"] == "Luffy"


def test_area_management(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    created = client.post("/v1/studies", params={"name": "foo", "version": 870})
    study_id = created.json()
    res_areas = client.get(f"/v1/studies/{study_id}/areas")
    assert res_areas.json() == [
        {
            "id": "all areas",
            "name": "All areas",
            "set": [],
            "thermals": None,
            "type": "DISTRICT",
        }
    ]

    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={"name": "area 1", "type": "AREA"},
    )
    assert res.status_code == 200, res.json()

    # Test area creation with duplicate name
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={
            "name": "Area 1",  # Same name but with different case
            "type": "AREA",
        },
    )
    assert res.status_code == 409, res.json()
    assert res.json() == {
        "description": "Area 'Area 1' already exists and could not be created",
        "exception": "DuplicateAreaName",
    }

    client.post(
        f"/v1/studies/{study_id}/areas",
        json={"name": "area 2", "type": "AREA"},
    )

    res = client.post(
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
    res.raise_for_status()

    client.post(
        f"/v1/studies/{study_id}/commands",
        json=[
            {
                "action": CommandName.CREATE_THERMAL_CLUSTER.value,
                "args": {
                    "area_id": "area 2",
                    "cluster_name": "cluster 2",
                    "parameters": {"nominalcapacity": 2.5},
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
            "name": "area 1",
            "set": None,
            "thermals": [
                {
                    "co2": 0.0,
                    "costGeneration": "SetManually",
                    "efficiency": 100.0,
                    "enabled": True,
                    "fixedCost": 0.0,
                    "genTs": "use global",
                    "group": "other 1",
                    "id": "cluster 1",
                    "lawForced": "uniform",
                    "lawPlanned": "uniform",
                    "marginalCost": 0.0,
                    "marketBidCost": 0.0,
                    "minDownTime": 1,
                    "minStablePower": 0.0,
                    "minUpTime": 1,
                    "mustRun": False,
                    "name": "cluster 1",
                    "nh3": 0.0,
                    "nmvoc": 0.0,
                    "nominalCapacity": 0.0,
                    "nox": 0.0,
                    "op1": 0.0,
                    "op2": 0.0,
                    "op3": 0.0,
                    "op4": 0.0,
                    "op5": 0.0,
                    "pm10": 0.0,
                    "pm25": 0.0,
                    "pm5": 0.0,
                    "so2": 0.0,
                    "spinning": 0.0,
                    "spreadCost": 0.0,
                    "startupCost": 0.0,
                    "unitCount": 1,
                    "variableOMCost": 0.0,
                    "volatilityForced": 0.0,
                    "volatilityPlanned": 0.0,
                }
            ],
            "type": "AREA",
        },
        {
            "id": "area 2",
            "name": "area 2",
            "set": None,
            "thermals": [
                {
                    "co2": 0.0,
                    "costGeneration": "SetManually",
                    "efficiency": 100.0,
                    "enabled": True,
                    "fixedCost": 0.0,
                    "genTs": "use global",
                    "group": "other 1",
                    "id": "cluster 2",
                    "lawForced": "uniform",
                    "lawPlanned": "uniform",
                    "marginalCost": 0.0,
                    "marketBidCost": 0.0,
                    "minDownTime": 1,
                    "minStablePower": 0.0,
                    "minUpTime": 1,
                    "mustRun": False,
                    "name": "cluster 2",
                    "nh3": 0.0,
                    "nmvoc": 0.0,
                    "nominalCapacity": 2.5,
                    "nox": 0.0,
                    "op1": 0.0,
                    "op2": 0.0,
                    "op3": 0.0,
                    "op4": 0.0,
                    "op5": 0.0,
                    "pm10": 0.0,
                    "pm25": 0.0,
                    "pm5": 0.0,
                    "so2": 0.0,
                    "spinning": 0.0,
                    "spreadCost": 0.0,
                    "startupCost": 0.0,
                    "unitCount": 1,
                    "variableOMCost": 0.0,
                    "volatilityForced": 0.0,
                    "volatilityPlanned": 0.0,
                }
            ],
            "type": "AREA",
        },
        {"id": "all areas", "name": "All areas", "set": ["area 1", "area 2"], "thermals": None, "type": "DISTRICT"},
    ]

    res = client.post(
        f"/v1/studies/{study_id}/links",
        json={
            "area1": "area 1",
            "area2": "area 2",
        },
    )
    res.raise_for_status()
    res_links = client.get(f"/v1/studies/{study_id}/links")
    assert res_links.json() == [
        {
            "area1": "area 1",
            "area2": "area 2",
            "assetType": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "displayComments": True,
            "comments": "",
            "filterSynthesis": "hourly, daily, weekly, monthly, annual",
            "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            "hurdlesCost": False,
            "linkStyle": "plain",
            "linkWidth": 1.0,
            "loopFlow": False,
            "transmissionCapacities": "enabled",
            "usePhaseShifter": False,
        }
    ]

    # -- `layers` integration tests

    res = client.get(f"/v1/studies/{study_id}/layers")
    res.raise_for_status()
    assert res.json() == [LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).model_dump(mode="json")]

    res = client.post(f"/v1/studies/{study_id}/layers?name=test")
    assert res.json() == "1"

    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).model_dump(mode="json"),
        LayerInfoDTO(id="1", name="test", areas=[]).model_dump(mode="json"),
    ]

    res = client.put(f"/v1/studies/{study_id}/layers/1?name=test2")
    assert res.status_code in {200, 201}, res.json()
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 1"])
    assert res.status_code in {200, 201}, res.json()
    res = client.put(f"/v1/studies/{study_id}/layers/1", json=["area 2"])
    assert res.status_code in {200, 201}, res.json()
    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).model_dump(mode="json"),
        LayerInfoDTO(id="1", name="test2", areas=["area 2"]).model_dump(mode="json"),
    ]

    # Delete the layer '1' that has 1 area
    res = client.delete(f"/v1/studies/{study_id}/layers/1")
    assert res.status_code == HTTPStatus.NO_CONTENT

    # Ensure the layer is deleted
    res = client.get(f"/v1/studies/{study_id}/layers")
    assert res.json() == [
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).model_dump(),
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
        LayerInfoDTO(id="0", name="All", areas=["area 1", "area 2"]).model_dump(),
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
        "spreadUnsuppliedEnergyCost": 0.0,
        "spreadSpilledEnergyCost": 0.0,
        "filterSynthesis": {"hourly", "daily", "weekly", "monthly", "annual"},
        "filterByYear": {"hourly", "daily", "weekly", "monthly", "annual"},
        "adequacyPatchMode": "outside",
    }

    res = client.put(
        f"/v1/studies/{study_id}/areas/area 1/properties/form",
        json={
            "energyCostUnsupplied": 2.0,
            "energyCostSpilled": 4.0,
            "nonDispatchPower": False,
            "dispatchHydroPower": False,
            "otherDispatchPower": False,
            "spreadUnsuppliedEnergyCost": -10.0,
            "spreadSpilledEnergyCost": 10.0,
            "filterSynthesis": ["monthly", "annual"],
            "filterByYear": ["hourly", "daily", "annual"],
            "adequacyPatchMode": "inside",
        },
    )
    res.raise_for_status()
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
        "spreadUnsuppliedEnergyCost": -10.0,
        "spreadSpilledEnergyCost": 10.0,
        "filterSynthesis": {"monthly", "annual"},
        "filterByYear": {"hourly", "daily", "annual"},
        "adequacyPatchMode": "inside",
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
        "group": "other res 1",
        "id": "cluster renewable 1",
        "name": "cluster renewable 1",  # Ensures we did not rename the cluster as we don't support it for now
        "nominalCapacity": 3.0,
        "tsInterpretation": "production-factor",
        "unitCount": 9,
    }
    assert res.status_code == 200, res.json()
    assert res.json() == expected

    # Thermal form

    obj = {
        "group": "lignite",
        "name": "cluster 1",
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

    client.put(
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
    assert result.json()["exception"] == "ReferencedObjectDeletionNotAllowed"

    # delete binding constraint 1
    client.delete(f"/v1/studies/{study_id}/bindingconstraints/binding%20constraint%201")
    # check now that we can delete the area 1
    result = client.delete(f"/v1/studies/{study_id}/areas/area%201")
    assert result.status_code == 200, res.json()
    res_areas = client.get(f"/v1/studies/{study_id}/areas")
    assert res_areas.json() == [
        {
            "id": "area 2",
            "name": "area 2",
            "set": None,
            "thermals": [
                {
                    "co2": 0.0,
                    "costGeneration": "SetManually",
                    "efficiency": 100.0,
                    "enabled": True,
                    "fixedCost": 0.0,
                    "genTs": "use global",
                    "group": "other 1",
                    "id": "cluster 2",
                    "lawForced": "uniform",
                    "lawPlanned": "uniform",
                    "marginalCost": 0.0,
                    "marketBidCost": 0.0,
                    "minDownTime": 1,
                    "minStablePower": 0.0,
                    "minUpTime": 1,
                    "mustRun": False,
                    "name": "cluster 2",
                    "nh3": 0.0,
                    "nmvoc": 0.0,
                    "nominalCapacity": 2.5,
                    "nox": 0.0,
                    "op1": 0.0,
                    "op2": 0.0,
                    "op3": 0.0,
                    "op4": 0.0,
                    "op5": 0.0,
                    "pm10": 0.0,
                    "pm25": 0.0,
                    "pm5": 0.0,
                    "so2": 0.0,
                    "spinning": 0.0,
                    "spreadCost": 0.0,
                    "startupCost": 0.0,
                    "unitCount": 1,
                    "variableOMCost": 0.0,
                    "volatilityForced": 0.0,
                    "volatilityPlanned": 0.0,
                }
            ],
            "type": "AREA",
        },
        {
            "id": "all areas",
            "name": "All areas",
            "set": ["area 2"],
            "thermals": None,
            "type": "DISTRICT",
        },
    ]


def test_archive(client: TestClient, admin_access_token: str, tmp_path: Path, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # =============================
    # OUTPUT PART
    # =============================

    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    outputs = res.json()
    fake_output = "fake_output"
    unarchived_outputs = [output["name"] for output in outputs if not output["archived"]]
    usual_output = unarchived_outputs[0]

    # Archive
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{fake_output}/_archive")
    assert res.json()["exception"] == "OutputNotFound"
    assert res.json()["description"] == f"Output '{fake_output}' not found"
    assert res.status_code == 404

    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{usual_output}/_archive")
    assert res.status_code == 200
    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
        ).json()["status"]
        == 3
    )

    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{usual_output}/_archive")
    assert res.json()["exception"] == "OutputAlreadyArchived"
    assert res.json()["description"] == f"Output '{usual_output}' is already archived"
    assert res.status_code == 417

    # Unarchive
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{fake_output}/_unarchive")
    assert res.json()["exception"] == "OutputNotFound"
    assert res.json()["description"] == f"Output '{fake_output}' not found"
    assert res.status_code == 404

    unarchived_output = unarchived_outputs[1]
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{unarchived_output}/_unarchive")
    assert res.json()["exception"] == "OutputAlreadyUnarchived"
    assert res.json()["description"] == f"Output '{unarchived_output}' is already unarchived"
    assert res.status_code == 417

    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{usual_output}/_unarchive")
    assert res.status_code == 200

    # =============================
    #  STUDY PART
    # =============================

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
    assert (tmp_path / "archive_dir" / f"{study_id}.7z").exists()

    res = client.put(f"/v1/studies/{study_id}/unarchive")

    task_id = res.json()
    wait_for(
        lambda: client.get(
            f"/v1/tasks/{task_id}",
        ).json()["status"]
        == 3,
    )

    res = client.get(f"/v1/studies/{study_id}")
    assert not res.json()["archived"]
    assert not (tmp_path / "archive_dir" / f"{study_id}.7z").exists()


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
        headers={"Authorization": f"Bearer {non_admin_credentials['access_token']}"},
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


def zip_study(src_path: Path, dest_path: Path) -> None:
    with zipfile.ZipFile(dest_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=2) as zipf:
        len_dir_path = len(str(src_path))
        for root, _, files in os.walk(src_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[len_dir_path:])


def test_import(client: TestClient, admin_access_token: str, internal_study_id: str, tmp_path: Path) -> None:
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
    georges_headers = {"Authorization": f"Bearer {george_credentials['access_token']}"}
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
        headers={"Authorization": f"Bearer {george_credentials['refresh_token']}"},
    )
    george_credentials = res.json()

    # George imports a study, and it should succeed even if he has only "READER" access in the group
    georges_headers = {"Authorization": f"Bearer {george_credentials['access_token']}"}
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
    res = client.post("/v1/studies/_import", files={"study": io.BytesIO(seven_zip_path.read_bytes())})
    assert res.status_code == 201

    # tests outputs import for .zip
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    client.post(
        f"/v1/studies/{internal_study_id}/output",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 7

    # tests outputs import for .7z
    output_path_seven_zip = ASSETS_DIR / "output_adq.7z"
    client.post(
        f"/v1/studies/{internal_study_id}/output",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        files={"output": io.BytesIO(output_path_seven_zip.read_bytes())},
    )
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert len(res.json()) == 8

    # test matrices import for .zip and .7z files
    matrices_zip_path = ASSETS_DIR / "matrices.zip"
    res_zip = client.post(
        "/v1/matrix/_import",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        files={"file": (matrices_zip_path.name, io.BytesIO(matrices_zip_path.read_bytes()), "application/zip")},
    )
    matrices_seven_zip_path = ASSETS_DIR / "matrices.7z"
    res_seven_zip = client.post(
        "/v1/matrix/_import",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
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

    # Creates a v9.2 study
    study_path = tmp_path / "test"
    app = CreateApp(study_dir=study_path, caption="A", version=StudyVersion.parse("9.2"), author="Unknown")
    app()

    # Zip it
    archive_path = tmp_path / "test.zip"
    zip_study(study_path, archive_path)
    # Asserts the import succeeds
    res = client.post("/v1/studies/_import", files={"study": io.BytesIO(archive_path.read_bytes())})
    assert res.status_code == 201

    # Modify the compatibility flag
    ini_path = study_path / "settings" / "generaldata.ini"
    ini_content = read_ini(ini_path)
    ini_content["compatibility"]["hydro-pmax"] = "hourly"
    write_ini_file(ini_path, ini_content)

    # Zip it again
    archive_path = tmp_path / "test2.zip"
    zip_study(study_path, archive_path)

    # Asserts the import fails
    res = client.post("/v1/studies/_import", files={"study": io.BytesIO(archive_path.read_bytes())})
    assert res.status_code == 422
    assert res.json()["exception"] == "StudyImportFailed"
    assert (
        res.json()["description"]
        == "Study 'A' could not be imported: AntaresWeb doesn't support the value 'hourly' for the flag 'hydro-pmax'"
    )


def test_import_with_editor(
    client: TestClient, admin_access_token: str, internal_study_id: str, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # 1. Create two users: 'creator' and 'importer'
    client.post("/v1/users", json={"name": "creator", "password": "password123"})
    client.post("/v1/users", json={"name": "importer", "password": "password456"})

    # Log in as 'creator'
    res_creator = client.post("/v1/login", json={"username": "creator", "password": "password123"})
    res_creator.raise_for_status()
    creator_creds = res_creator.json()
    creator_token = creator_creds["access_token"]

    # Log in as 'importer'
    res_importer = client.post("/v1/login", json={"username": "importer", "password": "password456"})
    res_importer.raise_for_status()
    importer_creds = res_importer.json()
    importer_token = importer_creds["access_token"]

    # 2. 'creator' creates a new study
    headers_creator = {"Authorization": f"Bearer {creator_token}"}
    study_name = "test_author_preservation"
    res_create = client.post(f"/v1/studies?name={study_name}", headers=headers_creator)
    res_create.raise_for_status()
    study_id = res_create.json()

    # 3. Verify that 'author' and 'editor' are set to 'creator'
    res_raw_initial = client.get(f"/v1/studies/{study_id}/raw?path=study", headers=headers_creator)
    initial_antares_data = res_raw_initial.json()["antares"]
    assert initial_antares_data["author"] == "creator"
    assert initial_antares_data["editor"] == "creator"

    # 4. Zip the study directory manually
    study_path = tmp_path / "internal_workspace" / study_id
    archive_path = tmp_path / f"{study_name}.zip"

    zip_study(study_path, archive_path)
    study_zip_data = archive_path.read_bytes()

    # 5. 'importer' imports the study
    headers_importer = {"Authorization": f"Bearer {importer_token}"}
    res_import = client.post(
        "/v1/studies/_import",
        files={"study": (f"{study_name}.zip", study_zip_data, "application/zip")},
        headers=headers_importer,
    )
    res_import.raise_for_status()
    imported_study_id = res_import.json()

    # 6. Verify 'author' is preserved and 'editor' is updated
    res_raw_imported = client.get(f"/v1/studies/{imported_study_id}/raw?path=study", headers=headers_importer)
    imported_antares_data = res_raw_imported.json()["antares"]
    assert imported_antares_data["author"] == "creator"
    assert imported_antares_data["editor"] == "importer"


def test_copy_with_editor_preservation(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # 1. Create a group and two users
    group_name = "test_copy_group"
    res = client.post("/v1/groups", json={"name": group_name})
    res.raise_for_status()
    group_id = res.json()["id"]

    client.post("/v1/users", json={"name": "creator_2", "password": "password123"})
    client.post("/v1/users", json={"name": "copier_2", "password": "password456"})

    # Log in as 'creator' to get ID
    res_creator = client.post("/v1/login", json={"username": "creator_2", "password": "password123"})
    res_creator.raise_for_status()
    creator_creds = res_creator.json()
    creator_id = creator_creds["user"]

    # Log in as 'copier' to get ID
    res_copier = client.post("/v1/login", json={"username": "copier_2", "password": "password456"})
    res_copier.raise_for_status()
    copier_creds = res_copier.json()
    copier_id = copier_creds["user"]

    # Add users to the group
    client.post(
        "/v1/roles",
        json={"type": 40, "group_id": group_id, "identity_id": creator_id},  # ADMIN
    )
    client.post(
        "/v1/roles",
        json={"type": 30, "group_id": group_id, "identity_id": copier_id},  # WRITER
    )

    # Refresh tokens to update permissions
    res_creator = client.post(
        "/v1/refresh",
        headers={"Authorization": f"Bearer {creator_creds['refresh_token']}"},
    )
    creator_creds = res_creator.json()
    creator_token = creator_creds["access_token"]

    res_copier = client.post(
        "/v1/refresh",
        headers={"Authorization": f"Bearer {copier_creds['refresh_token']}"},
    )
    copier_creds = res_copier.json()
    copier_token = copier_creds["access_token"]

    # 2. 'creator' creates a new study associated with the group
    headers_creator = {"Authorization": f"Bearer {creator_token}"}
    study_name = "test_author_preservation_on_copy"
    res_create = client.post(f"/v1/studies?name={study_name}&groups={group_id}", headers=headers_creator)
    res_create.raise_for_status()
    study_id = res_create.json()

    # 3. Verify that 'author' and 'editor' are set to 'creator'
    res_raw_initial = client.get(f"/v1/studies/{study_id}/raw?path=study", headers=headers_creator)
    initial_antares_data = res_raw_initial.json()["antares"]
    assert initial_antares_data["author"] == "creator_2"
    assert initial_antares_data["editor"] == "creator_2"

    # 4. 'copier' copies the study
    headers_copier = {"Authorization": f"Bearer {copier_token}"}
    copied_study_name = "copied_study_for_author_test"
    res_copy = client.post(
        f"/v1/studies/{study_id}/copy?study_name={copied_study_name}&use_task=false",
        headers=headers_copier,
    )
    res_copy.raise_for_status()
    copied_study_id = res_copy.json()

    # 5. Verify 'author' is preserved and 'editor' is updated in the copied study
    res_raw_copied = client.get(f"/v1/studies/{copied_study_id}/raw?path=study", headers=headers_copier)
    copied_antares_data = res_raw_copied.json()["antares"]
    assert copied_antares_data["author"] == "creator_2"
    assert copied_antares_data["editor"] == "copier_2"


def test_copy(client: TestClient, admin_access_token: str, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Copy a study with admin user who belongs to a group
    copied = client.post(f"/v1/studies/{internal_study_id}/copy?study_name=copied&use_task=false")
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
        f"/v1/studies/{internal_study_id}/copy?study_name=copied&use_task=false",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert copied.status_code == 201
    # asserts that it has no groups and PublicMode to READ
    res = client.get(f"/v1/studies/{copied.json()}").json()
    assert res["groups"] == []
    assert res["public_mode"] == "READ"

    # Copy a study with incorrect study name

    res = client.post(
        f"/v1/studies/{internal_study_id}/copy",
        params={
            "study_name": "copied=",
        },
    )
    assert res.status_code == 400
    assert res.json() == {
        "description": "study name copied= contains illegal characters (=, /)",
        "exception": "HTTPException",
    }


def test_copy_variant_as_raw(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create a Raw Study with 2 areas
    raw = client.post("/v1/studies?name=raw")
    assert raw.status_code == 201
    parent_id = raw.json()
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area1", "type": "AREA"},
    )
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area2", "type": "AREA"},
    )

    # Create a Variant from the Raw Study
    var = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "variant"})
    assert var.status_code == 200
    variant_id = var.json()
    variant_study = client.get(f"/v1/studies/{variant_id}")
    assert variant_study.status_code == 200

    # Copy Variant as a reference study
    client.post(f"/v1/studies/{variant_id}/copy?study_name=copied&use_task=False")

    all_studies = client.get("/v1/studies")
    assert variant_study.status_code == 200
    assert len(all_studies.json()) == 4

    copied_study = client.get("/v1/studies?name=copied")
    assert copied_study.status_code == 200
    copied_id = next(iter(copied_study.json()))

    # Check that the copied study contains all the datas
    copied_areas = client.get(f"/v1/studies/{copied_id}/areas")
    assert copied_areas.json() == client.get(f"/v1/studies/{parent_id}/areas").json()


def test_copy_with_jobs(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    raw = client.post("/v1/studies?name=raw")
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "use_task": False, "output_ids": ["output1"]},  # type: ignore
    )
    jobs_src_study = client.get(f"/v1/launcher/jobs?study={variant.json()}")
    assert jobs_src_study.status_code == 200
    copied_study = client.get("/v1/studies?name=copied")
    copied_id = next(iter(copied_study.json()))

    jobs_new_study = client.get(f"/v1/launcher/jobs?study={copied_id}")
    assert jobs_new_study.status_code == 200

    src_jobs = jobs_src_study.json()
    new_jobs = jobs_new_study.json()
    assert len(src_jobs) == len(new_jobs), "The number of jobs should be the same in both studies"

    # Compare each job, field by field
    for i, (src_job, new_job) in enumerate(zip(src_jobs, new_jobs)):
        # Verify IDs are different
        assert src_job["id"] != new_job["id"], f"Job {i}: IDs should be different"
        assert src_job["study_id"] != new_job["study_id"], f"Job {i}: study_ids should be different"

        # Compare all other fields
        for field in src_job.keys():
            if field not in ("id", "study_id"):
                assert src_job[field] == new_job[field], f"Job {i}: Field '{field}' does not match"


def test_copy_as_variant_with_outputs(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create a raw study and a variant
    raw = client.post("/v1/studies?name=raw")
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    # Create a fake output file
    output_file = tmp_path / "internal_workspace" / variant.json() / "output" / "output1" / "output.txt"
    output_file.parent.mkdir(parents=True)
    output_file.write_text("Output data")

    # Copy of the variant as a reference study
    copy = client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "with_outputs": True, "use_task": True, "output_ids": ["output1"]},  # type: ignore
    )
    client.get(f"/v1/tasks/{copy.json()}?wait_for_completion=True")

    copied_study = client.get("/v1/studies?name=copied")
    copied_id = next(iter(copied_study.json()))

    # The new study must contain an output fodler with the same data as the source variant study
    new_output_file = tmp_path / "internal_workspace" / copied_id / "output" / "output1" / "output.txt"
    assert output_file.read_text() == new_output_file.read_text()


def test_copy_variant_with_specific_path(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    raw = client.post("/v1/studies?name=raw")
    assert raw.status_code == 201
    parent_id = raw.json()
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area1", "type": "AREA"},
    )
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area2", "type": "AREA"},
    )
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    copy = client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "use_task": True, "destination_folder": "folder"},
    )
    client.get(f"/v1/tasks/{copy.json()}?wait_for_completion=True")

    copied_study = client.get("/v1/studies?name=copied").json()
    study_id = next(iter(copied_study))

    study_folder = copied_study[study_id]["folder"]
    assert study_folder == "folder/" + study_id


def test_copy_with_specific_output(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    raw = client.post("/v1/studies?name=raw")
    copy_with_output(client, tmp_path, raw.json())

    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})
    copy_with_output(client, tmp_path, variant.json())


def copy_with_output(client: TestClient, tmp_path: Path, study_id: str):
    output_base_dir = tmp_path / "internal_workspace" / study_id / "output"
    output_base_dir.mkdir(parents=True, exist_ok=True)

    for i in range(3):
        output_dir = output_base_dir / f"output{i}"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "result.txt").write_text(f"Output data for output{i}")

    # Copy a study with two outputs

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": True,
            "use_task": False,
            "output_ids": ["output0", "output1"],
        },
    )

    expected = ["output0", "output1"]
    folder = tmp_path / "internal_workspace" / res.json() / "output"

    for f in expected:
        dir_ = folder / f
        assert dir_.is_dir()
        assert (dir_ / "result.txt").exists()
    assert not (folder / "output2").exists()

    # Copy a study but with the with_output boolean set to False, should raise an error

    copy = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": False,
            "use_task": False,
            "output_ids": ["output2"],
        },
    )

    assert copy.status_code == 400
    assert copy.json() == {
        "description": "output_ids can only be used with with_outputs=True",
        "exception": "IncorrectArgumentsForCopy",
    }

    # Copy a study but without the outputs

    copy = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": False,
            "use_task": False,
        },
    )
    assert copy.status_code == 201

    # Copy a study with the boolean set but no id. Should copy all the outputs

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": True,
            "use_task": False,
        },
    )

    expected = ["output0", "output1", "output2"]
    folder = tmp_path / "internal_workspace" / res.json() / "output"
    for f in expected:
        dir_ = folder / f
        assert dir_.is_dir()
        assert (dir_ / "result.txt").exists()

    # Copy a study with no boolean and no id. Should not copy the outputs

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
        },
    )

    not_expected = ["output0", "output1", "output2"]
    folder = tmp_path / "internal_workspace" / res.json() / "output"

    for f in not_expected:
        dir_ = folder / f
        assert not dir_.exists()

    # Try to copy a non-existing output

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
            "with_outputs": True,
            "output_ids": ["output10"],
        },
    )
    assert res.status_code == 400
    assert res.json()["description"].startswith("Output folder output10 not found in")

    # Copy an output without the boolean set. The with_outputs boolean is implicitly True

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
            "output_ids": ["output1"],
        },
    )
    assert res.status_code == 201
    expected = "output1"
    folder = tmp_path / "internal_workspace" / res.json() / "output"
    dir_ = folder / expected
    assert dir_.is_dir()
    assert (dir_ / "result.txt").exists()


def test_areas_deletion_with_binding_constraints(
    client: TestClient, user_access_token: str, internal_study_id: str
) -> None:
    """
    Test the deletion of areas that are referenced in binding constraints.
    """

    # set client headers to user access token
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    area1_id = "france"
    area2_id = "germany"
    cluster_id = "nuclear power plant"

    constraint_terms = [
        {
            # Link between two areas
            "data": {"area1": area1_id, "area2": area2_id},
            "id": f"{area1_id}%{area2_id}",
            "offset": 2,
            "weight": 1.0,
        },
        {
            # Cluster in an area
            "data": {"area": area1_id, "cluster": cluster_id.lower()},
            "id": f"{area1_id}.{cluster_id.lower()}",
            "offset": 2,
            "weight": 1.0,
        },
    ]

    for constraint_term in constraint_terms:
        # Create an area "area_1" in the study
        res = client.post(
            f"/v1/studies/{internal_study_id}/areas",
            json={"name": area1_id.title(), "type": "AREA", "metadata": {"country": "FR"}},
        )
        res.raise_for_status()

        if set(constraint_term["data"]) == {"area1", "area2"}:
            # Create a second area and a link between the two areas
            res = client.post(
                f"/v1/studies/{internal_study_id}/areas",
                json={"name": area2_id.title(), "type": "AREA", "metadata": {"country": "DE"}},
            )
            res.raise_for_status()
            res = client.post(
                f"/v1/studies/{internal_study_id}/links",
                json={"area1": area1_id, "area2": area2_id},
            )
            res.raise_for_status()

        elif set(constraint_term["data"]) == {"area", "cluster"}:
            # Create a cluster in the first area
            res = client.post(
                f"/v1/studies/{internal_study_id}/areas/{area1_id}/clusters/thermal",
                json={"name": cluster_id.title(), "group": "Nuclear"},
            )
            res.raise_for_status()

        else:
            raise NotImplementedError(f"Unsupported constraint term: {constraint_term}")

        # create a binding constraint that references the link
        bc_id = "bc_1"
        bc_obj = {
            "name": bc_id,
            "enabled": True,
            "time_step": "daily",
            "operator": "less",
            "terms": [constraint_term],
        }
        res = client.post(f"/v1/studies/{internal_study_id}/bindingconstraints", json=bc_obj)
        res.raise_for_status()

        if set(constraint_term["data"]) == {"area1", "area2"}:
            areas_to_delete = [area1_id, area2_id]
        elif set(constraint_term["data"]) == {"area", "cluster"}:
            areas_to_delete = [area1_id]
        else:
            raise NotImplementedError(f"Unsupported constraint term: {constraint_term}")

        for area_id in areas_to_delete:
            # try to delete the areas
            res = client.delete(f"/v1/studies/{internal_study_id}/areas/{area_id}")
            assert res.status_code == 403, res.json()
            description = res.json()["description"]
            assert all([elm in description for elm in [area_id, bc_id]])
            assert res.json()["exception"] == "ReferencedObjectDeletionNotAllowed"

        # delete the binding constraint
        res = client.delete(f"/v1/studies/{internal_study_id}/bindingconstraints/{bc_id}")
        assert res.status_code == 200, res.json()

        for area_id in areas_to_delete:
            # delete the area
            res = client.delete(f"/v1/studies/{internal_study_id}/areas/{area_id}")
            assert res.status_code == 200, res.json()


def test_links_deletion_with_binding_constraints(
    client: TestClient, user_access_token: str, internal_study_id: str
) -> None:
    """
    Test the deletion of links that are referenced in binding constraints.
    """

    # set client headers to user access token
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create an area "area_1" in the study
    res = client.post(
        f"/v1/studies/{internal_study_id}/areas",
        json={
            "name": "area_1",
            "type": "AREA",
            "metadata": {"country": "FR"},
        },
    )
    assert res.status_code == 200, res.json()

    # Create an area "area_2" in the study
    res = client.post(
        f"/v1/studies/{internal_study_id}/areas",
        json={
            "name": "area_2",
            "type": "AREA",
            "metadata": {"country": "DE"},
        },
    )
    assert res.status_code == 200, res.json()

    # create a link between the two areas
    res = client.post(
        f"/v1/studies/{internal_study_id}/links",
        json={"area1": "area_1", "area2": "area_2"},
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
    res = client.post(f"/v1/studies/{internal_study_id}/bindingconstraints", json=bc_obj)
    assert res.status_code == 200, res.json()

    # try to delete the link before deleting the binding constraint
    res = client.delete(f"/v1/studies/{internal_study_id}/links/area_1/area_2")
    assert res.status_code == 403, res.json()
    description = res.json()["description"]
    assert all([elm in description for elm in ["area_1%area_2", "bc_1"]])
    assert res.json()["exception"] == "ReferencedObjectDeletionNotAllowed"

    # delete the binding constraint
    res = client.delete(f"/v1/studies/{internal_study_id}/bindingconstraints/bc_1")
    assert res.status_code == 200, res.json()

    # delete the link
    res = client.delete(f"/v1/studies/{internal_study_id}/links/area_1/area_2")
    assert res.status_code == 200, res.json()
