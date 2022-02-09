import time
from typing import Callable
from pathlib import Path
from unittest.mock import ANY

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.study.business.area_management import AreaType
from antarest.study.model import MatrixIndex, StudyDownloadLevelDTO


def wait_for(predicate: Callable[[], bool], timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if predicate():
                return
        except Exception as e:
            pass
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

    # study creation
    created = client.post(
        "/v1/studies?name=foo",
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

    # Study copy
    copied = client.post(
        f"/v1/studies/{created.json()}/copy?dest=copied&use_task=false",
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
        json={"type": 20, "group_id": group_id, "identity_id": 2},
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
        json={"name": "STA-mini-copy", "status": "copied", "horizon": "2035"},
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
        f"/v1/matrix",
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
        f"/v1/matrixdataset",
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
        f"/v1/matrixdataset/_search?name=myda",
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
            "metadata": {"country": None},
            "name": "All areas",
            "set": [],
            "thermals": None,
            "type": "DISTRICT",
        }
    ]

    client.post(
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

    res_areas = client.get(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_areas.json() == [
        {
            "id": "area 1",
            "metadata": {"country": "FR"},
            "name": "area 1",
            "set": None,
            "thermals": [],
            "type": "AREA",
        },
        {
            "id": "area 2",
            "metadata": {"country": "DE"},
            "name": "area 2",
            "set": None,
            "thermals": [],
            "type": "AREA",
        },
        {
            "id": "all areas",
            "metadata": {"country": None},
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
        f"/v1/studies/{study_id}/links",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_links.json() == [{"area1": "area 1", "area2": "area 2"}]
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
    assert res.status_code == 200
    res_ui = client.get(
        f"/v1/studies/{study_id}/raw?path=input/areas/area%201/ui/ui",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_ui.json() == {
        "x": 100,
        "y": 100,
        "color_r": 255,
        "color_g": 0,
        "color_b": 100,
        "layers": 0,
    }

    client.delete(
        f"/v1/studies/{study_id}/areas/area%201",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    res_areas = client.get(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res_areas.json() == [
        {
            "id": "area 2",
            "metadata": {"country": "DE"},
            "name": "area 2",
            "set": None,
            "thermals": [],
            "type": "AREA",
        },
        {
            "id": "all areas",
            "metadata": {"country": None},
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
        f"/v1/core/maintenance/message",
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
