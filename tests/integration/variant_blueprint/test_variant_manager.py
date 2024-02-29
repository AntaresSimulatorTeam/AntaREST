import io
import logging
import time

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from tests.integration.assets import ASSETS_DIR


def test_variant_manager(client: TestClient, admin_access_token: str, study_id: str, caplog) -> None:
    with caplog.at_level(level=logging.WARNING):
        admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

        base_study_res = client.post("/v1/studies?name=foo", headers=admin_headers)

        base_study_id = base_study_res.json()

        res = client.post(f"/v1/studies/{base_study_id}/variants?name=foo", headers=admin_headers)
        variant_id = res.json()

        client.post(f"/v1/launcher/run/{variant_id}", headers=admin_headers)

        res = client.get(f"v1/studies/{variant_id}/synthesis", headers=admin_headers)

        assert variant_id in res.json()["output_path"]

        client.post(f"/v1/studies/{variant_id}/variants?name=bar", headers=admin_headers)
        client.post(f"/v1/studies/{variant_id}/variants?name=baz", headers=admin_headers)
        res = client.get(f"/v1/studies/{base_study_id}/variants", headers=admin_headers)
        children = res.json()
        assert children["node"]["name"] == "foo"
        assert len(children["children"]) == 1
        assert children["children"][0]["node"]["name"] == "foo"
        assert len(children["children"][0]["children"]) == 2
        assert children["children"][0]["children"][0]["node"]["name"] == "bar"
        assert children["children"][0]["children"][1]["node"]["name"] == "baz"

        # George creates a base study
        # He creates a variant from this study : assert that no command is created
        # The admin creates a variant from the same base study : assert that its author is admin (created via a command)

        client.post(
            "/v1/users",
            headers=admin_headers,
            json={"name": "George", "password": "mypass"},
        )
        res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
        george_credentials = res.json()
        base_study_res = client.post(
            "/v1/studies?name=foo",
            headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        )

        base_study_id = base_study_res.json()
        res = client.post(
            f"/v1/studies/{base_study_id}/variants?name=foo_2",
            headers={"Authorization": f'Bearer {george_credentials["access_token"]}'},
        )
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 0
        res = client.post(f"/v1/studies/{base_study_id}/variants?name=foo", headers=admin_headers)
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 1
        command = res.json()[0]
        assert command["action"] == "update_config"
        assert command["args"]["target"] == "study"
        assert command["args"]["data"]["antares"]["author"] == "admin"

        res = client.get(f"/v1/studies/{variant_id}/parents", headers=admin_headers)
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
            headers=admin_headers,
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
            headers=admin_headers,
        )
        assert res.status_code == 200

        res = client.post(
            f"/v1/studies/{variant_id}/command",
            json={
                "action": "create_area",
                "args": {"area_name": "testZone3", "metadata": {}},
            },
            headers=admin_headers,
        )
        assert res.status_code == 200

        command_id = res.json()
        res = client.put(
            f"/v1/studies/{variant_id}/commands/{command_id}",
            json={
                "action": "create_area",
                "args": {"area_name": "testZone4", "metadata": {}},
            },
            headers=admin_headers,
        )
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 4
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
            headers=admin_headers,
        )
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 2
        assert res.status_code == 200

        command_id = res.json()[1]["id"]

        res = client.put(f"/v1/studies/{variant_id}/commands/{command_id}/move?index=0", headers=admin_headers)
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert res.json()[0]["id"] == command_id
        assert res.status_code == 200

        res = client.delete(f"/v1/studies/{variant_id}/commands/{command_id}", headers=admin_headers)

        assert res.status_code == 200

        res = client.put(f"/v1/studies/{variant_id}/generate", headers=admin_headers)
        assert res.status_code == 200

        res = client.get(f"/v1/tasks/{res.json()}?wait_for_completion=true", headers=admin_headers)
        assert res.status_code == 200
        task_result = TaskDTO.parse_obj(res.json())
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result.success  # type: ignore

        res = client.get(f"/v1/studies/{variant_id}", headers=admin_headers)
        assert res.status_code == 200

        res = client.post(f"/v1/studies/{variant_id}/freeze?name=bar", headers=admin_headers)
        assert res.status_code == 500

        new_study_id = "newid"

        res = client.get(f"/v1/studies/{new_study_id}", headers=admin_headers)
        assert res.status_code == 404

        res = client.delete(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert res.status_code == 200
        assert len(res.json()) == 0

        res = client.delete(f"/v1/studies/{variant_id}", headers=admin_headers)
        assert res.status_code == 200

        res = client.get(f"/v1/studies/{variant_id}", headers=admin_headers)
        assert res.status_code == 404


def test_comments(client: TestClient, admin_access_token: str, variant_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Put comments
    comment = "updated comment"
    res = client.put(f"/v1/studies/{variant_id}/comments", json={"comments": comment}, headers=admin_headers)
    assert res.status_code == 204

    # Asserts comments are updated
    res = client.get(f"/v1/studies/{variant_id}/comments", headers=admin_headers)
    assert res.json() == comment

    # Generates the study
    res = client.put(f"/v1/studies/{variant_id}/generate?denormalize=false&from_scratch=true", headers=admin_headers)
    task_id = res.json()
    # Wait for task completion
    res = client.get(f"/v1/tasks/{task_id}", headers=admin_headers, params={"wait_for_completion": True})
    assert res.status_code == 200
    task_result = TaskDTO.parse_obj(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result is not None
    assert task_result.result.success

    # Asserts comments did not disappear
    res = client.get(f"/v1/studies/{variant_id}/comments", headers=admin_headers)
    assert res.json() == comment


def test_recursive_variant_tree(client: TestClient, admin_access_token: str, base_study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}
    parent_id = base_study_id
    for k in range(200):
        res = client.post(
            f"/v1/studies/{base_study_id}/variants",
            headers=admin_headers,
            params={"name": f"variant_{k}"},
        )
        base_study_id = res.json()

    # Asserts that we do not trigger a Recursive Exception
    res = client.get(f"/v1/studies/{parent_id}/variants", headers=admin_headers)
    assert res.status_code == 200, res.json()


def test_outputs(client: TestClient, admin_access_token: str, variant_id: str, tmp_path: str) -> None:
    # =======================
    #  SET UP
    # =======================

    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Only done to generate the variant folder
    res = client.post(f"/v1/launcher/run/{variant_id}", headers=admin_headers)
    res.raise_for_status()
    job_id = res.json()["job_id"]

    status = client.get(f"/v1/launcher/jobs/{job_id}", headers=admin_headers).json()["status"]
    while status != "failed":
        time.sleep(0.2)
        status = client.get(f"/v1/launcher/jobs/{job_id}", headers=admin_headers).json()["status"]

    # Import an output to the study folder
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    res = client.post(
        f"/v1/studies/{variant_id}/output",
        headers=admin_headers,
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    res.raise_for_status()

    # =======================
    #  ASSERTS GENERATING THE VARIANT DOES NOT `HIDE` OUTPUTS FROM THE ENDPOINT
    # =======================

    # Get output
    res = client.get(f"/v1/studies/{variant_id}/outputs", headers=admin_headers)
    assert res.status_code == 200, res.json()
    outputs = res.json()
    assert len(outputs) == 1

    # Generates the study
    res = client.put(
        f"/v1/studies/{variant_id}/generate",
        headers=admin_headers,
        params={"denormalize": False, "from_scratch": True},
    )
    res.raise_for_status()
    task_id = res.json()

    # Wait for task completion
    res = client.get(f"/v1/tasks/{task_id}", headers=admin_headers, params={"wait_for_completion": True})
    res.raise_for_status()
    task_result = TaskDTO.parse_obj(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result is not None
    assert task_result.result.success

    # Get outputs again
    res = client.get(f"/v1/studies/{variant_id}/outputs", headers=admin_headers)
    assert res.status_code == 200, res.json()
    outputs = res.json()
    assert len(outputs) == 1
