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
import os
import zipfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion
from tests.test_helpers.dates import utc_to_local
from tests.test_helpers.download import download_to_file

EXPECTED_DATE = utc_to_local("20201014-1227")


@pytest.fixture
def empty_study_id(admin_client: TestClient) -> str:
    """Creates a blank study and returns its ID."""
    res = admin_client.post(
        "/v1/studies",
        params={"name": "My study"},
    )
    assert res.status_code == 201, res.json()
    return res.json()


@pytest.fixture
def output_and_study(admin_client: TestClient, empty_study_id: str, output_zip: Path) -> tuple[str, str]:
    """Study with the 20201014-1427ec output imported in V2 storage"""
    res = admin_client.post(
        f"/v1/studies/{empty_study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    output_name = res.json()
    assert output_name == f"{EXPECTED_DATE}eco"
    return empty_study_id, output_name


@pytest.fixture
def study_id(output_and_study: tuple[str, str]) -> str:
    return output_and_study[0]


@pytest.fixture
def output_name(output_and_study: tuple[str, str]) -> str:
    return output_and_study[1]


def test_import(admin_client: TestClient, empty_study_id: str, output_zip: Path) -> None:
    client = admin_client
    study_id = empty_study_id

    # Import an output and store it with new storage type
    res = admin_client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    output_name = res.json()
    assert output_name == f"{EXPECTED_DATE}eco"

    # Check output metadata
    res = client.get(
        f"/v1/studies/{study_id}/outputs",
    )
    assert res.status_code == 200, res.json()
    assert len(res.json()) == 1
    assert res.json()[-1] == {
        "archived": False,
        "byYear": False,
        "mode": "Economy",
        "name": f"{EXPECTED_DATE}eco",
        "nbYears": 1,
        "synthesis": True,
        "storageType": "V2",
    }, res.json()


def test_import_duplicate(admin_client: TestClient, study_id: str, output_zip: Path) -> None:
    """Importing the same output twice should fail."""
    client = admin_client

    # Import again — should fail (conflict or server error due to DB uniqueness constraint)
    res = client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_zip.read_bytes())},
    )
    assert res.status_code != 202, "Duplicate import should not succeed"


def test_delete_output(admin_client: TestClient, study_id: str, output_name: str) -> None:
    """Test deleting a V2 output through the API."""
    client = admin_client

    # Verify it exists
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.status_code == 200
    v2_outputs = [o for o in res.json() if o["name"] == output_name]
    assert len(v2_outputs) == 1

    # Delete
    res = client.delete(f"/v1/studies/{study_id}/outputs/{output_name}")
    assert res.status_code == 200

    # Verify it's gone
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.status_code == 200
    v2_outputs = [o for o in res.json() if o["name"] == output_name]
    assert len(v2_outputs) == 0


def test_delete_nonexistent_output(admin_client: TestClient, empty_study_id: str) -> None:
    """Deleting a non-existent V2 output should return 404."""
    res = admin_client.delete(f"/v1/studies/{empty_study_id}/outputs/nonexistent-output")
    assert res.status_code == 404


def test_delete_then_reimport(admin_client: TestClient, study_id: str, output_name: str, output_zip: Path) -> None:
    """After deleting a V2 output, reimporting the same one should succeed."""
    client = admin_client

    # Delete
    res = client.delete(f"/v1/studies/{study_id}/outputs/{output_name}")
    assert res.status_code == 200

    # Reimport — should succeed, proving cleanup (DB + archive storage) was complete
    res = client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    output_name_2 = res.json()
    assert output_name_2 == output_name


def test_delete_study_linked_to_output(admin_client: TestClient, study_id: str) -> None:
    client = admin_client

    # Check output metadata
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert len(res.json()) == 1

    # Delete study
    res = client.delete(f"/v1/studies/{study_id}")
    assert res.status_code == 200


def test_archive_and_unarchive(admin_client: TestClient, study_id: str, output_name: str, tmp_path: Path) -> None:
    """Test archiving and unarchiving a V2 output."""
    client = admin_client

    output_archives_dir = tmp_path / "output_archives"

    # Check the archive is already present in the expected dir
    # Checks an implementation detail, but allows to verify the config is correcly taken into account
    files = os.listdir(output_archives_dir)
    assert len(files) == 1
    assert files[0] == f"{study_id}-{output_name}"

    # Verify not archived initially
    res = client.get(f"/v1/studies/{study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is False

    # Archive
    res = client.post(f"/v1/studies/{study_id}/outputs/{output_name}/_archive")
    assert res.status_code == 200, res.json()
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(client, None, task_id)
    assert task.status == TaskStatus.COMPLETED

    # Verify archived
    res = client.get(f"/v1/studies/{study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is True

    # Archiving again should fail (417 EXPECTATION_FAILED)
    res = client.post(f"/v1/studies/{study_id}/outputs/{output_name}/_archive")
    assert res.status_code == 417

    # Unarchive
    res = client.post(f"/v1/studies/{study_id}/outputs/{output_name}/_unarchive")
    assert res.status_code == 200, res.json()
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(client, None, task_id)
    assert task.status == TaskStatus.COMPLETED

    # Verify unarchived
    res = client.get(f"/v1/studies/{study_id}/outputs")
    v2_output = next(o for o in res.json() if o["name"] == output_name)
    assert v2_output["archived"] is False

    # Unarchiving again should fail (417 EXPECTATION_FAILED)
    res = client.post(f"/v1/studies/{study_id}/outputs/{output_name}/_unarchive")
    assert res.status_code == 417


def test_get_time_index(admin_client: TestClient, study_id: str, output_name: str) -> None:
    """Test retrieving the time index at various frequencies for a V2 output."""
    client = admin_client

    # Hourly (default)
    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/time-index?frequency=hourly")
    assert res.status_code == 200, res.json()
    assert res.json() == {"first_week_size": 7, "level": "hourly", "start_date": "2018-01-01 00:00:00", "steps": 168}

    # Daily
    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/time-index?frequency=daily")
    assert res.status_code == 200, res.json()
    assert res.json() == {"first_week_size": 7, "level": "daily", "start_date": "2018-01-01 00:00:00", "steps": 7}

    # Weekly
    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/time-index?frequency=weekly")
    assert res.status_code == 200, res.json()
    assert res.json() == {"first_week_size": 7, "level": "weekly", "start_date": "2018-01-01 00:00:00", "steps": 1}

    # Monthly
    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/time-index?frequency=monthly")
    assert res.status_code == 200, res.json()
    assert res.json() == {"first_week_size": 7, "level": "monthly", "start_date": "2018-01-01 00:00:00", "steps": 1}

    # Annual
    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/time-index?frequency=annual")
    assert res.status_code == 200, res.json()
    assert res.json() == {"first_week_size": 7, "level": "annual", "start_date": "2018-01-01 00:00:00", "steps": 1}


def test_get_variables_list(admin_client: TestClient, study_id: str, output_name: str) -> None:
    """Test retrieving the variables list for a V2 output."""
    client = admin_client

    res = client.get(f"/v1/studies/{study_id}/output/{output_name}/variables-list")
    assert res.status_code == 200, res.json()
    data = res.json()

    assert "mcAll" in data
    assert "mcInd" in data

    mc_all = data["mcAll"]
    assert "areas" in mc_all
    assert "links" in mc_all

    assert [area["name"] for area in mc_all["areas"]] == ["de", "es"]
    assert [link["name"] for link in mc_all["links"]] == []


def test_export_output(admin_client: TestClient, study_id: str, output_name: str, tmp_path: Path) -> None:
    """Test exporting a V2 output."""
    client = admin_client

    res = client.get(f"/v1/studies/{study_id}/outputs/{output_name}/export")
    assert res.status_code == 200, res.json()
    data = res.json()
    assert "task" in data
    assert "file" in data

    download_id = data["file"]["id"]
    download_to_file(client, download_id, tmp_path / "output.zip")

    with zipfile.ZipFile(tmp_path / "output.zip", "r") as f:
        assert len(f.namelist()) == 79


def test_get_variables_information(admin_client: TestClient, study_id: str, output_name: str) -> None:
    """Test retrieving the variables information endpoint for a V2 output."""
    client = admin_client

    res = client.get(f"/v1/studies/{study_id}/outputs/{output_name}/variables")
    assert res.status_code == 200, res.json()
    data = res.json()

    # No mc-ind in that output --> empty
    # TODO: add some test with non empty data
    assert data == {"area": [], "link": []}


FAKE_OUTPUT = "nonexistent-output"


def test_time_index_nonexistent_output(admin_client: TestClient, empty_study_id: str) -> None:
    """Getting time index for a non-existent output should return 404."""
    res = admin_client.get(f"/v1/studies/{empty_study_id}/output/{FAKE_OUTPUT}/time-index?frequency=hourly")
    assert res.status_code == 404


def test_variables_list_nonexistent_output(admin_client: TestClient, empty_study_id: str) -> None:
    """Getting variables list for a non-existent output should return 404."""
    res = admin_client.get(f"/v1/studies/{empty_study_id}/output/{FAKE_OUTPUT}/variables-list")
    assert res.status_code == 404


def test_export_nonexistent_output(admin_client: TestClient, admin_access_token: str, empty_study_id: str) -> None:
    """Exporting a non-existent output creates a task that fails."""
    res = admin_client.get(f"/v1/studies/{empty_study_id}/outputs/{FAKE_OUTPUT}/export")
    # The endpoint creates a background task, so it returns 200 immediately
    assert res.status_code == 200
    task_id = res.json()["task"]
    task = wait_task_completion(admin_client, admin_access_token, task_id)
    assert task.status == TaskStatus.FAILED


def test_archive_nonexistent_output(admin_client: TestClient, empty_study_id: str) -> None:
    """Archiving a non-existent output should return 404."""
    res = admin_client.post(f"/v1/studies/{empty_study_id}/outputs/{FAKE_OUTPUT}/_archive")
    assert res.status_code == 404


def test_unarchive_nonexistent_output(admin_client: TestClient, empty_study_id: str) -> None:
    """Unarchiving a non-existent output should return 404."""
    res = admin_client.post(f"/v1/studies/{empty_study_id}/outputs/{FAKE_OUTPUT}/_unarchive")
    assert res.status_code == 404


def test_conversion_to_v2(admin_client: TestClient, output_zip: Path, empty_study_id: str) -> None:
    """Test conversion of an output to V2 storage."""
    client = admin_client
    study_id = empty_study_id

    res = client.post(
        f"/v1/studies/{study_id}/output",
        files={"output": io.BytesIO(output_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    output_name = res.json()
    assert output_name == f"{EXPECTED_DATE}eco"

    res = client.post(
        f"/v1/studies/{study_id}/output/{output_name}/_convert?storage_type=V2",
    )
    assert res.status_code == 200, res.json()

    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.json() == [
        {
            "archived": False,
            "byYear": False,
            "mode": "Economy",
            "name": f"{EXPECTED_DATE}eco",
            "nbYears": 1,
            "synthesis": True,
            "storageType": "V2",
        }
    ]

    # Second conversion should fail
    res = client.post(
        f"/v1/studies/{study_id}/output/{output_name}/_convert?storage_type=V2",
    )
    assert res.status_code == 400, res.json()
