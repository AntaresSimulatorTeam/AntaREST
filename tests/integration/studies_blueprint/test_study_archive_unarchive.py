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
import zipfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from tests.integration.studies_blueprint.utils import check_minimal_study_integrity, create_minimal_study
from tests.integration.utils import wait_for


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
    wait_for(lambda: client.get(f"/v1/tasks/{task_id}").json()["status"] == 3)

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

    # Drop a fake in-study output to ensure it survives archive/unarchive.
    study_path = tmp_path / "internal_workspace" / study_id
    outputs_path = study_path / "output"
    outputs_path.mkdir(parents=True, exist_ok=True)

    fake_output_dir = outputs_path / "20240101-0000eco"
    fake_output_dir.mkdir()
    fake_output_file = fake_output_dir / "simulation.log"
    fake_output_file.write_text("Simulation done")

    fake_zipped_output = outputs_path / "20240201-0000eco.zip"
    with zipfile.ZipFile(fake_zipped_output, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("simulation.log", data="Zipped simulation done")

    res = client.put(f"/v1/studies/{study_id}/archive")
    assert res.status_code == 200
    task_id = res.json()
    wait_for(lambda: client.get(f"/v1/tasks/{task_id}").json()["status"] == 3)

    res = client.get(f"/v1/studies/{study_id}")
    assert res.json()["archived"]
    assert (tmp_path / "archive_dir" / f"{study_id}.7z").exists()

    res = client.put(f"/v1/studies/{study_id}/unarchive")

    task_id = res.json()
    wait_for(lambda: client.get(f"/v1/tasks/{task_id}").json()["status"] == 3)

    res = client.get(f"/v1/studies/{study_id}")
    assert not res.json()["archived"]
    assert not (tmp_path / "archive_dir" / f"{study_id}.7z").exists()
    assert fake_output_file.exists()
    assert fake_output_file.read_text() == "Simulation done"
    assert fake_zipped_output.is_file()
    with zipfile.ZipFile(fake_zipped_output) as zf:
        assert zf.read("simulation.log").decode() == "Zipped simulation done"


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
def test_archive_with_both_storage_modes(
    client: TestClient, user_access_token: str, storage_mode: str, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a Raw study with several areas, links, constraints, thermals ...
    res = client.post(f"/v1/studies?name=MyStudy&storage_mode={storage_mode}")
    assert res.status_code == 201
    study_id = res.json()

    create_minimal_study(client, study_id)

    # Archive the study
    res = client.put(f"/v1/studies/{study_id}/archive")
    assert res.status_code == 200
    task_id = res.json()
    client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")

    # Ensures that the archive exists
    assert (tmp_path / "archive_dir" / f"{study_id}.7z").exists()

    # Ensures the DB / FS was cleaned
    assert not (tmp_path / "internal_workspace" / study_id).exists()
    # todo for the BD check

    # Unarchive the study
    res = client.put(f"/v1/studies/{study_id}/unarchive")
    assert res.status_code == 200
    task_id = res.json()
    client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")

    # Ensures we can fetch the data correctly
    check_minimal_study_integrity(client, study_id)
