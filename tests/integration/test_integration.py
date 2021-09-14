import time
from pathlib import Path

from fastapi import FastAPI
from starlette.testclient import TestClient


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
        f"/v1/studies/{created.json()}/copy?dest=copied",
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

    matrix = {
        "index": ["1", "2"],
        "columns": ["a", "b"],
        "data": [[1, 2], [3, 4]],
    }

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
            "type": "CLUSTER",
        }
    ]

    res_create = client.post(
        f"/v1/studies/{study_id}/areas",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "test", "type": "AREA"},
    )
    res_update = client.put(
        f"/v1/studies/{study_id}/areas/test",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
        json={"name": "test", "type": "AREA"},
    )
    res_delete = client.delete(
        f"/v1/studies/{study_id}/areas/test",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert (
        res_create.status_code == 500
        and res_create.json()["exception"] == "NotImplementedError"
    )
    assert (
        res_update.status_code == 500
        and res_update.json()["exception"] == "NotImplementedError"
    )
    assert (
        res_delete.status_code == 500
        and res_delete.json()["exception"] == "NotImplementedError"
    )


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
    assert res.status_code == 200

    res = client.get(
        f"/v1/studies/{base_study_id}/variants",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert len(res.json()) == 1
    assert res.status_code == 200

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
        f"/v1/studies/{variant_id}/commands/{command_id}?index=0",
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

    # new_study_id = res.json()
    new_study_id = "newid"

    res = client.get(
        f"/v1/studies/{new_study_id}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    assert res.status_code == 404

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
