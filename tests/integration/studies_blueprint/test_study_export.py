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
from io import BytesIO
from pathlib import Path

from starlette.testclient import TestClient

from tests.integration.utils import wait_task_completion
from tests.test_helpers.download import download_to_file
from tests.test_helpers.outputs import create_minimal_output_zip_from_name


def _zip_namelist(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as zip_file:
        return set(zip_file.namelist())


# Doing exports with both .zip and .7z
def test_export_study_with_both_compression(admin_client: TestClient, internal_study_id: str, tmp_path) -> None:
    client = admin_client

    base_path = tmp_path / "tmp"
    # exporting without any parameters (thus exporting in .zip by default)
    export_res = client.get(f"/v1/studies/{internal_study_id}/export")
    json_export_download_id = export_res.json()["file"]["id"]

    download_to_file(client, json_export_download_id, base_path / "export.zip")

    # exporting with the .7z compression
    export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.7z")

    json_export_download_id = export_res.json()["file"]["id"]

    download_to_file(client, json_export_download_id, base_path / "export.zip")

    # exporting with an unauthorized compression
    failed_export_res = client.get(f"/v1/studies/{internal_study_id}/export?compression=.rar")
    assert failed_export_res.status_code == 422, failed_export_res


# Doing exports with both .zip and .7z
def test_export_study_outputs(admin_client: TestClient, tmp_path) -> None:
    client = admin_client
    raw = client.post("/v1/studies?name=raw")
    export_with_output_test(client, raw.json(), tmp_path)

    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})
    export_with_output_test(client, variant.json(), tmp_path)


def export_with_output_test(client: TestClient, study_id: str, tmp_path: Path) -> None:
    # Create 3 outputs in provided study
    for output_name in ["20201002-1023eco-output1", "20210716-1815adq-output2", "20231002-1023eco"]:
        buffer = BytesIO()
        create_minimal_output_zip_from_name(buffer, output_name)
        upload = client.post(f"/v1/studies/{study_id}/output", files={"output": (f"{output_name}.zip", buffer)})
        assert upload.status_code == 202

    # Archive one of the outputs
    archive = client.post(f"/v1/studies/{study_id}/outputs/20231002-1023eco/_archive")
    assert archive.status_code == 200
    task_id = archive.json()
    wait_task_completion(client, None, task_id)

    # Check they are correctly created
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.status_code == 200
    assert [(d["name"], d["archived"]) for d in res.json()] == [
        ("20201002-1023eco-output1", False),
        ("20210716-1815adq-output2", False),
        ("20231002-1023eco", True),
    ]

    # Export the study without outputs
    res = client.get(
        f"/v1/studies/{study_id}/export",
        params={
            "no_output": True,
        },
    )
    assert res.status_code == 200
    download_id = res.json()["file"]["id"]

    # Check outputs have not been exported
    download_to_file(client, download_id, tmp_path / "export.zip")
    namelist = _zip_namelist(tmp_path / "export.zip")
    assert not any(name.startswith("output") for name in namelist)

    # Export the study with outputs
    res = client.get(
        f"/v1/studies/{study_id}/export",
        params={
            "no_output": False,
        },
    )
    assert res.status_code == 200
    download_id = res.json()["file"]["id"]

    # Check all outputs have been exported
    download_to_file(client, download_id, tmp_path / "export.zip")
    namelist = _zip_namelist(tmp_path / "export.zip")
    assert "output/20201002-1023eco-output1/info.antares-output" in namelist
    assert "output/20210716-1815adq-output2/info.antares-output" in namelist
    assert "output/20231002-1023eco/info.antares-output" in namelist
