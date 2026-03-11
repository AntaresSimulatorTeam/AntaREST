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
import io
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_task_completion


def _import_v2_output(client: TestClient, study_id: str) -> str:
    """Helper: import the output_adq.zip as V2 storage for the given study.
    Returns the output name."""
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    res = client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    output_name = res.json()
    assert output_name == "20221004-1430adq"
    return output_name


def test_import(admin_client: TestClient, internal_study_id: str, tmp_path: Path) -> None:
    client = admin_client

    # Import an output and store it with new storage type
    _import_v2_output(client, internal_study_id)

    # Check output metadata
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs",
    )
    assert res.status_code == 200, res.json()
    assert len(res.json()) == 7
    assert res.json()[-1] == {
        "archived": False,
        "byYear": False,
        "mode": "Adequacy",
        "name": "20221004-1430adq",
        "nbYears": 1,
        "synthesis": True,
    }, res.json()


def test_import_duplicate(admin_client: TestClient, internal_study_id: str) -> None:
    """Importing the same output twice should fail."""
    client = admin_client
    _import_v2_output(client, internal_study_id)

    # Import again — should fail (conflict or server error due to DB uniqueness constraint)
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    res = client.post(
        f"/v1/studies/{internal_study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    assert res.status_code != 202, "Duplicate import should not succeed"


def test_delete_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Test deleting a V2 output through the API."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    # Verify it exists
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert res.status_code == 200
    v2_outputs = [o for o in res.json() if o["name"] == output_name]
    assert len(v2_outputs) == 1

    # Delete
    res = client.delete(f"/v1/studies/{internal_study_id}/outputs/{output_name}")
    assert res.status_code == 200

    # Verify it's gone
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert res.status_code == 200
    v2_outputs = [o for o in res.json() if o["name"] == output_name]
    assert len(v2_outputs) == 0


def test_delete_nonexistent_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Deleting a non-existent V2 output should return 404."""
    res = admin_client.delete(f"/v1/studies/{internal_study_id}/outputs/nonexistent-output")
    assert res.status_code == 404


def test_delete_then_reimport(admin_client: TestClient, internal_study_id: str) -> None:
    """After deleting a V2 output, reimporting the same one should succeed."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    # Delete
    res = client.delete(f"/v1/studies/{internal_study_id}/outputs/{output_name}")
    assert res.status_code == 200

    # Reimport — should succeed, proving cleanup (DB + archive storage) was complete
    output_name_2 = _import_v2_output(client, internal_study_id)
    assert output_name_2 == output_name


def test_delete_study_linked_to_output(admin_client: TestClient, internal_study_id: str, tmp_path: Path) -> None:
    client = admin_client

    # Creates a blank study
    res = client.post(
        "/v1/studies",
        params={"name": "My study"},
    )
    assert res.status_code == 201, res.json()
    study_id = res.json()

    # Import an output and store it with new storage type
    _import_v2_output(client, study_id)

    # Check output metadata
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert len(res.json()) == 1

    # Delete study
    res = client.delete(f"/v1/studies/{study_id}")
    assert res.status_code == 200


def test_archive_and_unarchive(admin_client: TestClient, admin_access_token: str, internal_study_id: str) -> None:
    """Test archiving and unarchiving a V2 output."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    # Verify not archived initially
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is False

    # Archive
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_name}/_archive")
    assert res.status_code == 200, res.json()
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(client, admin_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED

    # Verify archived
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is True

    # Archiving again should fail (417 EXPECTATION_FAILED)
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_name}/_archive")
    assert res.status_code == 417

    # Unarchive
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_name}/_unarchive")
    assert res.status_code == 200, res.json()
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(client, admin_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED

    # Verify unarchived
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is False

    # Unarchiving again should fail (417 EXPECTATION_FAILED)
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_name}/_unarchive")
    assert res.status_code == 417


def test_get_time_index(admin_client: TestClient, internal_study_id: str) -> None:
    """Test retrieving the time index at various frequencies for a V2 output."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    # Hourly (default)
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/time-index?frequency=hourly")
    assert res.status_code == 200, res.json()
    hourly_data = res.json()
    assert hourly_data["level"] == "hourly"
    assert hourly_data["steps"] > 0
    assert "start_date" in hourly_data

    # Daily
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/time-index?frequency=daily")
    assert res.status_code == 200, res.json()
    daily_data = res.json()
    assert daily_data["level"] == "daily"
    assert daily_data["steps"] > 0
    # Daily steps should be less than hourly
    assert daily_data["steps"] < hourly_data["steps"]

    # Weekly
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/time-index?frequency=weekly")
    assert res.status_code == 200, res.json()
    assert res.json()["level"] == "weekly"

    # Monthly
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/time-index?frequency=monthly")
    assert res.status_code == 200, res.json()
    assert res.json()["level"] == "monthly"

    # Annual
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/time-index?frequency=annual")
    assert res.status_code == 200, res.json()
    assert res.json()["level"] == "annual"
    assert res.json()["steps"] == 1


def test_get_variables_list(admin_client: TestClient, internal_study_id: str) -> None:
    """Test retrieving the variables list for a V2 output."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_name}/variables-list")
    assert res.status_code == 200, res.json()
    data = res.json()

    # The output_adq.zip is an Adequacy mode output: the variables list extractor
    # currently only scans economy/ mode, so the result is empty for this output.
    assert "mcAll" in data
    assert "mcInd" in data

    mc_all = data["mcAll"]
    assert "areas" in mc_all
    assert "links" in mc_all


def test_export_output(admin_client: TestClient, admin_access_token: str, internal_study_id: str) -> None:
    """Test exporting a V2 output."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_name}/export")
    assert res.status_code == 200, res.json()
    data = res.json()
    assert "task" in data
    assert "file" in data

    # Wait for export task to complete
    task_id = data["task"]
    task = wait_task_completion(client, admin_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED


def test_get_variables_information(admin_client: TestClient, internal_study_id: str) -> None:
    """Test retrieving the variables information endpoint for a V2 output."""
    client = admin_client
    output_name = _import_v2_output(client, internal_study_id)

    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_name}/variables")
    assert res.status_code == 200, res.json()
    data = res.json()

    # Should return variables information with areas and links structure
    assert isinstance(data, dict)


FAKE_OUTPUT = "nonexistent-output"


def test_time_index_nonexistent_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Getting time index for a non-existent output should return 404."""
    res = admin_client.get(f"/v1/studies/{internal_study_id}/output/{FAKE_OUTPUT}/time-index?frequency=hourly")
    assert res.status_code == 404


def test_variables_list_nonexistent_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Getting variables list for a non-existent output should return 404."""
    res = admin_client.get(f"/v1/studies/{internal_study_id}/output/{FAKE_OUTPUT}/variables-list")
    assert res.status_code == 404


def test_export_nonexistent_output(admin_client: TestClient, admin_access_token: str, internal_study_id: str) -> None:
    """Exporting a non-existent output creates a task that fails."""
    res = admin_client.get(f"/v1/studies/{internal_study_id}/outputs/{FAKE_OUTPUT}/export")
    # The endpoint creates a background task, so it returns 200 immediately
    assert res.status_code == 200
    task_id = res.json()["task"]
    task = wait_task_completion(admin_client, admin_access_token, task_id)
    assert task.status == TaskStatus.FAILED


def test_archive_nonexistent_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Archiving a non-existent output should return 404."""
    res = admin_client.post(f"/v1/studies/{internal_study_id}/outputs/{FAKE_OUTPUT}/_archive")
    assert res.status_code == 404


def test_unarchive_nonexistent_output(admin_client: TestClient, internal_study_id: str) -> None:
    """Unarchiving a non-existent output should return 404."""
    res = admin_client.post(f"/v1/studies/{internal_study_id}/outputs/{FAKE_OUTPUT}/_unarchive")
    assert res.status_code == 404
