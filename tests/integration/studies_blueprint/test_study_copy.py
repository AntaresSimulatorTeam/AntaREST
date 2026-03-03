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
from io import BytesIO
from pathlib import Path

from integration.test_helpers.outputs import create_minimal_output_zip_from_name
from starlette.testclient import TestClient


def test_copy_with_editor_preservation(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # 1. Create a group and two users
    group_name = "test_copy_group"
    res = client.post("/v1/groups", json={"name": group_name})
    res.raise_for_status()
    group_id = res.json()["id"]

    client.post("/v1/users", json={"name": "creator_2", "password": "password123"})
    client.post("/v1/users", json={"name": "copier_2", "password": "password456"})

    # Log in as 'creator' to get ID
    res_creator = client.post("/v1/login", json={"username": "creator_2", "password": "password123"})
    res_creator.raise_for_status()
    creator_creds = res_creator.json()
    creator_id = creator_creds["user"]

    # Log in as 'copier' to get ID
    res_copier = client.post("/v1/login", json={"username": "copier_2", "password": "password456"})
    res_copier.raise_for_status()
    copier_creds = res_copier.json()
    copier_id = copier_creds["user"]

    # Add users to the group
    client.post(
        "/v1/roles",
        json={"type": 40, "group_id": group_id, "identity_id": creator_id},  # ADMIN
    )
    client.post(
        "/v1/roles",
        json={"type": 30, "group_id": group_id, "identity_id": copier_id},  # WRITER
    )

    # Refresh tokens to update permissions
    res_creator = client.post(
        "/v1/refresh",
        headers={"Authorization": f"Bearer {creator_creds['refresh_token']}"},
    )
    creator_creds = res_creator.json()
    creator_token = creator_creds["access_token"]

    res_copier = client.post(
        "/v1/refresh",
        headers={"Authorization": f"Bearer {copier_creds['refresh_token']}"},
    )
    copier_creds = res_copier.json()
    copier_token = copier_creds["access_token"]

    # 2. 'creator' creates a new study associated with the group
    headers_creator = {"Authorization": f"Bearer {creator_token}"}
    study_name = "test_author_preservation_on_copy"
    res_create = client.post(f"/v1/studies?name={study_name}&groups={group_id}", headers=headers_creator)
    res_create.raise_for_status()
    study_id = res_create.json()

    # 3. Verify that 'author' and 'editor' are set to 'creator'
    res_raw_initial = client.get(f"/v1/studies/{study_id}/raw?path=study", headers=headers_creator)
    initial_antares_data = res_raw_initial.json()["antares"]
    assert initial_antares_data["author"] == "creator_2"
    assert initial_antares_data["editor"] == "creator_2"

    # 4. 'copier' copies the study
    headers_copier = {"Authorization": f"Bearer {copier_token}"}
    copied_study_name = "copied_study_for_author_test"
    res_copy = client.post(
        f"/v1/studies/{study_id}/copy?study_name={copied_study_name}&use_task=false",
        headers=headers_copier,
    )
    res_copy.raise_for_status()
    copied_study_id = res_copy.json()

    # 5. Verify 'author' is preserved and 'editor' is updated in the copied study
    res_raw_copied = client.get(f"/v1/studies/{copied_study_id}/raw?path=study", headers=headers_copier)
    copied_antares_data = res_raw_copied.json()["antares"]
    assert copied_antares_data["author"] == "creator_2"
    assert copied_antares_data["editor"] == "copier_2"


def test_copy(client: TestClient, admin_access_token: str, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Copy a study with admin user who belongs to a group
    copied = client.post(f"/v1/studies/{internal_study_id}/copy?study_name=copied&use_task=false")
    assert copied.status_code == 201
    # asserts that it has admin groups and PublicMode to NONE
    res = client.get(f"/v1/studies/{copied.json()}").json()
    assert res["groups"] == [{"id": "admin", "name": "admin"}]
    assert res["public_mode"] == "NONE"

    # Connect with user George who belongs to no group
    res = client.post("/v1/login", json={"username": "George", "password": "mypass"})
    george_credentials = res.json()

    # George copies a study
    copied = client.post(
        f"/v1/studies/{internal_study_id}/copy?study_name=copied&use_task=false",
        headers={"Authorization": f"Bearer {george_credentials['access_token']}"},
    )
    assert copied.status_code == 201
    # asserts that it has no groups and PublicMode to READ
    res = client.get(f"/v1/studies/{copied.json()}").json()
    assert res["groups"] == []
    assert res["public_mode"] == "READ"

    # Copy a study with incorrect study name

    res = client.post(
        f"/v1/studies/{internal_study_id}/copy",
        params={
            "study_name": "copied=",
        },
    )
    assert res.status_code == 400
    assert res.json() == {
        "description": "study name copied= contains illegal characters (=, /)",
        "exception": "HTTPException",
    }


def test_copy_variant_as_raw(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create a Raw Study with 2 areas
    raw = client.post("/v1/studies?name=raw")
    assert raw.status_code == 201
    parent_id = raw.json()
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area1", "type": "AREA"},
    )
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area2", "type": "AREA"},
    )

    # Create a Variant from the Raw Study
    var = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "variant"})
    assert var.status_code == 200
    variant_id = var.json()
    variant_study = client.get(f"/v1/studies/{variant_id}")
    assert variant_study.status_code == 200

    # Copy Variant as a reference study
    client.post(f"/v1/studies/{variant_id}/copy?study_name=copied&use_task=False")

    all_studies = client.get("/v1/studies")
    assert variant_study.status_code == 200
    assert len(all_studies.json()) == 4

    copied_study = client.get("/v1/studies?name=copied")
    assert copied_study.status_code == 200
    copied_id = next(iter(copied_study.json()))

    # Check that the copied study contains all the datas
    copied_areas = client.get(f"/v1/studies/{copied_id}/areas")
    assert copied_areas.json() == client.get(f"/v1/studies/{parent_id}/areas").json()


def test_copy_with_jobs(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    raw = client.post("/v1/studies?name=raw")
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "use_task": False, "output_ids": ["output1"]},
    )
    jobs_src_study = client.get(f"/v1/launcher/jobs?study={variant.json()}")
    assert jobs_src_study.status_code == 200
    copied_study = client.get("/v1/studies?name=copied")
    copied_id = next(iter(copied_study.json()))

    jobs_new_study = client.get(f"/v1/launcher/jobs?study={copied_id}")
    assert jobs_new_study.status_code == 200

    src_jobs = jobs_src_study.json()
    new_jobs = jobs_new_study.json()
    assert len(src_jobs) == len(new_jobs), "The number of jobs should be the same in both studies"

    # Compare each job, field by field
    for i, (src_job, new_job) in enumerate(zip(src_jobs, new_jobs)):
        # Verify IDs are different
        assert src_job["id"] != new_job["id"], f"Job {i}: IDs should be different"
        assert src_job["study_id"] != new_job["study_id"], f"Job {i}: study_ids should be different"

        # Compare all other fields
        for field in src_job.keys():
            if field not in ("id", "study_id"):
                assert src_job[field] == new_job[field], f"Job {i}: Field '{field}' does not match"


def test_copy_as_variant_with_outputs(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # Create a raw study and a variant
    raw = client.post("/v1/studies?name=raw")
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    # Create a fake output file
    output_path = tmp_path / "internal_workspace" / variant.json() / "output"
    output_file = output_path / "output1" / "output.txt"
    output_file.parent.mkdir(parents=True)
    output_file.write_text("Output data")

    # Create a fake zipped output
    output_zip_file = output_path / "output2.zip"
    output_zip_file.touch()

    # Copy of the variant as a reference study
    copy = client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "with_outputs": True, "output_ids": ["output1", "output2"]},
    )
    client.get(f"/v1/tasks/{copy.json()}?wait_for_completion=True")

    copied_study = client.get("/v1/studies?name=copied")
    copied_id = next(iter(copied_study.json()))

    # The new study must contain an output folder with the same data as the source variant study
    new_output_path = tmp_path / "internal_workspace" / copied_id / "output"
    new_output_file = new_output_path / "output1" / "output.txt"
    assert output_file.read_text() == new_output_file.read_text()
    assert (new_output_path / "output2.zip").exists()


def test_copy_variant_with_specific_path(client: TestClient, admin_access_token: str, tmp_path: Path) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    raw = client.post("/v1/studies?name=raw")
    assert raw.status_code == 201
    parent_id = raw.json()
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area1", "type": "AREA"},
    )
    client.post(
        f"/v1/studies/{parent_id}/areas",
        json={"name": "area2", "type": "AREA"},
    )
    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})

    copy = client.post(
        f"/v1/studies/{variant.json()}/copy",
        params={"study_name": "copied", "use_task": True, "destination_folder": "folder"},
    )
    client.get(f"/v1/tasks/{copy.json()}?wait_for_completion=True")

    copied_study = client.get("/v1/studies?name=copied").json()
    study_id = next(iter(copied_study))

    study_folder = copied_study[study_id]["folder"]
    assert study_folder == "folder/" + study_id


def test_copy_with_specific_output(admin_client: TestClient, internal_study_id: str, tmp_path: Path) -> None:
    client = admin_client
    raw = client.post("/v1/studies?name=raw")
    copy_with_output_test(client, raw.json())

    variant = client.post(f"/v1/studies/{raw.json()}/variants", params={"name": "variant"})
    copy_with_output_test(client, variant.json())


def copy_with_output_test(client: TestClient, study_id: str) -> None:
    # Create 3 outputs in provided study
    for output_name in ["20201002-1023eco-output1", "20210716-1815adq-output2", "20231002-1023eco"]:
        buffer = BytesIO()
        create_minimal_output_zip_from_name(buffer, output_name)
        upload = client.post(f"/v1/studies/{study_id}/output", files={"output": (f"{output_name}.zip", buffer)})
        assert upload.status_code == 202

    # Archive one of the outputs
    archive = client.post(f"/v1/studies/{study_id}/outputs/20231002-1023eco/_archive")
    assert archive.status_code == 200

    # Check they are correctly created
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.status_code == 200
    assert [(d["name"], d["archived"]) for d in res.json()] == [
        ("20201002-1023eco-output1", False),
        ("20210716-1815adq-output2", False),
        ("20231002-1023eco", True),
    ]

    # Copy a study with two outputs
    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": True,
            "use_task": False,
            "output_ids": ["20210716-1815adq-output2", "20231002-1023eco"],
        },
    )

    copied_study_id = res.json()
    res = client.get(f"/v1/studies/{copied_study_id}/outputs")
    assert res.status_code == 200
    assert [d["name"] for d in res.json()] == ["20210716-1815adq-output2", "20231002-1023eco"]

    # Copy a study but with the with_output boolean set to False, should raise an error
    copy = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": False,
            "use_task": False,
            "output_ids": ["20201014-1427eco"],
        },
    )

    assert copy.status_code == 400
    assert copy.json() == {
        "description": "output_ids can only be used with with_outputs=True",
        "exception": "IncorrectArgumentsForCopy",
    }

    # Copy a study but without the outputs

    copy = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": False,
            "use_task": False,
        },
    )
    assert copy.status_code == 201

    # Copy a study with the boolean set but no id. Should copy all the outputs

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "with_outputs": True,
            "use_task": False,
        },
    )

    res = client.get(f"/v1/studies/{res.json()}/outputs")
    assert res.status_code == 200
    assert [d["name"] for d in res.json()] == [
        "20201002-1023eco-output1",
        "20210716-1815adq-output2",
        "20231002-1023eco",
    ]

    # Copy a study with no boolean and no id. Should not copy the outputs
    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
        },
    )

    res = client.get(f"/v1/studies/{res.json()}/outputs")
    assert res.status_code == 200
    assert [d["name"] for d in res.json()] == []

    # Try to copy a non-existing output
    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
            "with_outputs": True,
            "output_ids": ["output10"],
        },
    )
    assert res.status_code == 404
    assert res.json()["description"].startswith("Output 'output10' not found"), res.json()

    # Copy an output without the boolean set. The with_outputs boolean is implicitly True

    res = client.post(
        f"/v1/studies/{study_id}/copy",
        params={
            "study_name": "copied",
            "use_task": False,
            "output_ids": ["20231002-1023eco"],
        },
    )
    assert res.status_code == 201
    res = client.get(f"/v1/studies/{res.json()}/outputs")
    assert res.status_code == 200
    assert [d["name"] for d in res.json()] == ["20231002-1023eco"]
