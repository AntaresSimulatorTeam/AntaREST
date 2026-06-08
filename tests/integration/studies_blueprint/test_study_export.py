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
from unittest.mock import ANY

import pytest
from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import read_ini
from tests.integration.studies_blueprint.utils import create_minimal_study
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


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
def test_export_with_both_storage_modes(
    client: TestClient, user_access_token: str, storage_mode: str, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a Raw study with several areas, links, constraints, thermals ...
    res = client.post(f"/v1/studies?name=MyStudy&storage_mode={storage_mode}")
    assert res.status_code == 201
    study_id = res.json()

    create_minimal_study(client, study_id)

    # Export the study
    res = client.get(f"/v1/studies/{study_id}/export")
    assert res.status_code == 200
    download_id = res.json()["file"]["id"]

    zip_path = tmp_path / "export.zip"
    download_to_file(client, download_id, tmp_path / zip_path)
    assert zip_path.exists()

    study_path = tmp_path / "exported_study"
    with zipfile.ZipFile(zip_path) as zip_output:
        zip_output.extractall(path=study_path)

    assert study_path.exists()

    # Check the path content to be sure the study was correctly exported
    study_antares = read_ini(study_path / "study.antares")
    assert study_antares == {
        "antares": {
            "version": 9.3,
            "caption": "MyStudy",
            "author": "George",
            "editor": "George",
            "created": ANY,
            "lastsave": ANY,
        }
    }

    # Areas
    assert sorted([f.name for f in (study_path / "input" / "areas").iterdir()]) == [
        "be",
        "ch",
        "fr",
        "list.txt",
        "sets.ini",
    ]
    # Links
    assert sorted([f.name for f in (study_path / "input" / "links").iterdir()]) == ["be", "ch", "fr"]
    # Thermals
    ini_path = study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini"
    ini_content = read_ini(ini_path)
    assert sorted(ini_content) == ["lignite plant", "nuclear cluster"]
    # Binding constraints
    ini_path = study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    ini_content = read_ini(ini_path)
    assert ini_content == {
        "0": {
            "id": "constraint1",
            "name": "Constraint1",
            "enabled": True,
            "type": "hourly",
            "operator": "equal",
            "comments": "",
            "filter-year-by-year": "",
            "filter-synthesis": "",
            "group": "default",
            "be%ch": 4.0,
        }
    }
