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

from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp
from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from tests.integration.assets import ASSETS_DIR
from tests.integration.studies_blueprint.utils import check_minimal_study_integrity, create_minimal_study


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
            "file": (
                matrices_seven_zip_path.name,
                io.BytesIO(matrices_seven_zip_path.read_bytes()),
                "application/zip",
            )
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

    # Asserts the import success
    res = client.post("/v1/studies/_import", files={"study": io.BytesIO(archive_path.read_bytes())})
    assert res.status_code == 201


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


def test_import_with_both_storage_modes(client: TestClient, user_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a Raw FS study with several areas, links, constraints, thermals ...
    study_name = "MyStudy"
    res = client.post(f"/v1/studies?name={study_name}")
    assert res.status_code == 201
    study_id = res.json()

    create_minimal_study(client, study_id)

    # Zip the study directory manually
    study_path = tmp_path / "internal_workspace" / study_id
    archive_path = tmp_path / f"{study_name}.zip"

    zip_study(study_path, archive_path)
    study_zip_data = archive_path.read_bytes()

    # Imports the study with both storage modes
    for storage_mode in ["filesystem", "database"]:
        content = {"study": (f"{study_name}.zip", study_zip_data, "application/zip")}

        res_import = client.post(f"/v1/studies/_import?storage_mode={storage_mode}", files=content)
        res_import.raise_for_status()
        imported_study_id = res_import.json()

        # Ensures the data was imported correctly
        check_minimal_study_integrity(client, imported_study_id)
