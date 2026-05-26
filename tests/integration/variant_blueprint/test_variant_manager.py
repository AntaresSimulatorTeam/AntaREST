# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import datetime
import io
import logging
import time
import typing as t
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.study.model import Study
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_task_completion


@pytest.fixture(name="base_study_id")
def base_study_id_fixture(client: TestClient, admin_access_token: str, caplog: t.Any) -> str:
    """Create a base study and return its ID."""
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}
    with caplog.at_level(level=logging.WARNING):
        res = client.post("/v1/studies?name=Base1", headers=admin_headers)
    return t.cast(str, res.json())


@pytest.fixture(name="variant_id")
def variant_id_fixture(
    client: TestClient,
    admin_access_token: str,
    base_study_id: str,
    caplog: t.Any,
) -> str:
    """Create a variant and return its ID."""
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}
    with caplog.at_level(level=logging.WARNING):
        res = client.post(f"/v1/studies/{base_study_id}/variants?name=Variant1", headers=admin_headers)
    return t.cast(str, res.json())


@pytest.fixture(name="generate_snapshots")
def generate_snapshot_fixture(
    client: TestClient,
    admin_access_token: str,
    base_study_id: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: t.Any,
) -> t.List[str]:
    """Generate some snapshots with different date of update and last access"""

    # Initialize variant_ids list
    variant_ids = []

    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    with caplog.at_level(level=logging.WARNING):
        # Generate three different timestamp
        now = current_time()
        older_time = now - datetime.timedelta(hours=25)  # older than the default value which is 24
        old_time = now - datetime.timedelta(hours=8)  # older than 6 hours
        recent_time = now - datetime.timedelta(hours=2)  # older than 0 hours

        for index, different_time in enumerate([older_time, old_time, recent_time]):
            res = client.post(f"/v1/studies/{base_study_id}/variants?name=variant{index}", headers=admin_headers)
            variant_id = res.json()
            variant_ids.append(variant_id)

            # Generate snapshot for each variant
            task_id = client.put(f"/v1/studies/{variant_ids[index]}/generate", headers=admin_headers)
            wait_task_completion(client, admin_access_token, task_id.json())  # wait for the filesystem to be updated
            client.get(f"v1/studies/{variant_ids[index]}", headers=admin_headers)

            # Modify the `created_at` and `updated_at` attributes in DB.
            with db():
                variant = db.session.get(Study, variant_id)
                variant.last_access = different_time
                variant.updated_at = different_time
                db.session.merge(variant)
                db.session.commit()

    return t.cast(t.List[str], variant_ids)


def test_variant_manager(
    client: TestClient,
    admin_access_token: str,
    base_study_id: str,
    variant_id: str,
    caplog: t.Any,
) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    with caplog.at_level(level=logging.WARNING):
        client.post(f"/v1/launcher/run/{variant_id}", headers=admin_headers)

        res = client.get(f"v1/studies/{variant_id}/synthesis", headers=admin_headers)

        assert res.json()["study_id"] == variant_id

        client.post(f"/v1/studies/{variant_id}/variants?name=bar", headers=admin_headers)
        client.post(f"/v1/studies/{variant_id}/variants?name=baz", headers=admin_headers)
        res = client.get(f"/v1/studies/{base_study_id}/variants", headers=admin_headers)
        children = res.json()
        assert children["node"]["name"] == "Base1"
        assert len(children["children"]) == 1
        assert children["children"][0]["node"]["name"] == "Variant1"
        assert len(children["children"][0]["children"]) == 2
        # Variant children are sorted by creation date in reverse order
        assert children["children"][0]["children"][0]["node"]["name"] == "baz"
        assert children["children"][0]["children"][1]["node"]["name"] == "bar"

        # George creates a base study
        # He creates a variant from this study : assert that no command is created and the editor is still George.
        # The admin does the same : assert that no command is created and the editor is now the admin.

        client.post(
            "/v1/users",
            headers=admin_headers,
            json={"name": "George", "password": "mypass"},
        )
        res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
        george_credentials = res.json()
        base_study_res = client.post(
            "/v1/studies?name=foo",
            headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        )

        base_study_id = base_study_res.json()

        # George part
        res = client.post(
            f"/v1/studies/{base_study_id}/variants?name=foo_2",
            headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
        )
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 0
        res = client.get(f"/v1/studies/{variant_id}/raw?path=study", headers=admin_headers)
        antares_content = res.json()["antares"]
        assert antares_content["author"] == "George"
        assert antares_content["editor"] == "George"

        # Admin part
        res = client.post(f"/v1/studies/{base_study_id}/variants?name=foo", headers=admin_headers)
        variant_id = res.json()
        res = client.get(f"/v1/studies/{variant_id}/commands", headers=admin_headers)
        assert len(res.json()) == 0

        res = client.get(f"/v1/studies/{variant_id}/raw?path=study", headers=admin_headers)
        antares_content = res.json()["antares"]
        assert antares_content["author"] == "George"
        assert antares_content["editor"] == "admin"

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
        task_result = TaskDTO.model_validate(res.json())
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result.success  # type: ignore

        res = client.get(f"/v1/studies/{variant_id}", headers=admin_headers)
        assert res.status_code == 200

        new_study_id = "new_id"

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


def test_create_variant_inherits_parent_directory_id(
    client: TestClient,
    admin_access_token: str,
) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    res = client.post("/v1/studies?name=BaseWithDirectory&directory=project/subfolder", headers=admin_headers)
    assert res.status_code == 201
    base_study_id = res.json()

    res = client.get(f"/v1/studies/{base_study_id}", headers=admin_headers)
    assert res.status_code == 200
    parent_study = res.json()
    assert parent_study["directory_id"] is not None

    res = client.post(f"/v1/studies/{base_study_id}/variants?name=VariantWithDirectory", headers=admin_headers)
    assert res.status_code == 200
    variant_id = res.json()

    res = client.get(f"/v1/studies/{variant_id}", headers=admin_headers)
    assert res.status_code == 200
    variant_study = res.json()
    assert variant_study["parent_id"] == base_study_id
    assert variant_study["directory_id"] == parent_study["directory_id"]


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
    task_result = TaskDTO.model_validate(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result is not None
    assert task_result.result.success

    # Asserts comments did not disappear
    res = client.get(f"/v1/studies/{variant_id}/comments", headers=admin_headers)
    assert res.json() == comment


def test_recursive_variant_tree(client: TestClient, admin_access_token: str, base_study_id: str) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}
    parent_id = base_study_id
    leaf_id = base_study_id
    for k in range(200):
        res = client.post(
            f"/v1/studies/{leaf_id}/variants",
            headers=admin_headers,
            params={"name": f"variant_{k}"},
        )
        leaf_id = res.json()

    # Asserts that we do not trigger a Recursive Exception
    res = client.get(f"/v1/studies/{parent_id}/variants", headers=admin_headers)
    assert res.status_code == 200, res.json()

    # `from_root=true` from the deepest variant returns the same tree as querying the root.
    res = client.get(f"/v1/studies/{leaf_id}/variants", params={"from_root": True}, headers=admin_headers)
    assert res.status_code == 200, res.json()
    assert res.json()["node"]["id"] == parent_id


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
    task_result = TaskDTO.model_validate(res.json())
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result is not None
    assert task_result.result.success

    # Get outputs again
    res = client.get(f"/v1/studies/{variant_id}/outputs", headers=admin_headers)
    assert res.status_code == 200, res.json()
    outputs = res.json()
    assert len(outputs) == 1


def test_clear_snapshots(
    client: TestClient,
    admin_access_token: str,
    tmp_path: Path,
    generate_snapshots: t.List[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The `snapshot/` directory must not exist after a call to `clear-snapshot`.
    """
    # Set up
    admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

    older = Path(tmp_path).joinpath("internal_workspace", generate_snapshots[0], "snapshot")
    old = Path(tmp_path).joinpath("internal_workspace", generate_snapshots[1], "snapshot")
    recent = Path(tmp_path).joinpath("internal_workspace", generate_snapshots[2], "snapshot")

    # Test
    # Check initial data
    assert older.exists() and old.exists() and recent.exists()

    # Delete the older snapshot (default retention hours implicitly equals to 24 hours)
    # and check if it was successfully deleted
    response = client.put("v1/studies/variants/clear-snapshots", headers=admin_headers)
    task = response.json()
    wait_task_completion(client, admin_access_token, task)
    assert (not older.exists()) and old.exists() and recent.exists()

    # Delete the old snapshot and check if it was successfully deleted
    response = client.put("v1/studies/variants/clear-snapshots?hours=6", headers=admin_headers)
    task = response.json()
    wait_task_completion(client, admin_access_token, task)
    assert (not older.exists()) and (not old.exists()) and recent.exists()

    # Delete the recent snapshot and check if it was successfully deleted
    response = client.put("v1/studies/variants/clear-snapshots?hours=-1", headers=admin_headers)
    task = response.json()
    wait_task_completion(client, admin_access_token, task)
    assert not (older.exists() and old.exists() and recent.exists())


def test_deletion_while_generating(client: TestClient, admin_access_token: str, variant_id: str, tmp_path: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}
    # Generates the study from scratch
    res = client.put(f"/v1/studies/{variant_id}/generate?from_scratch=True")
    res.raise_for_status()
    # Deletes it without waiting for the generation to end
    res = client.delete(f"/v1/studies/{variant_id}")
    # Ensures the deletion succeeds
    assert res.status_code == 200
    assert not (tmp_path / "internal_workspace" / variant_id).exists()
