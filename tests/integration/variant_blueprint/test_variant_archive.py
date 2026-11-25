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

from starlette.testclient import TestClient

from tests.integration.utils import wait_task_completion


def _create_variant(client: TestClient, parent_id: str, name: str) -> str:
    res = client.post(f"/v1/studies/{parent_id}/variants?name={name}")
    res.raise_for_status()
    variant_id: str = res.json()
    # Create an area (with a name unique in the lineage) to generate the snapshot
    client.post(f"/v1/studies/{variant_id}/areas", json={"name": f"area_{name}"}).raise_for_status()
    return variant_id


def _is_archived(client: TestClient, study_id: str) -> bool:
    res = client.get(f"/v1/studies/{study_id}")
    res.raise_for_status()
    archived: bool = res.json()["archived"]
    return archived


def test_archive_variant_and_its_descendants(
    admin_client: TestClient, admin_access_token: str, tmp_path: Path, output_zip: Path
) -> None:
    client = admin_client
    workspace = tmp_path / "internal_workspace"
    archives = tmp_path / "archive_dir"

    # Study tree: raw -> v1 -> v2 -> v3
    raw_id = client.post("/v1/studies?name=raw").json()
    v1_id = _create_variant(client, raw_id, "v1")
    v2_id = _create_variant(client, v1_id, "v2")
    v3_id = _create_variant(client, v2_id, "v3")

    # Give a real output to each variant
    output_id = "20201014-1427eco"
    for variant_id in (v1_id, v2_id, v3_id):
        with zipfile.ZipFile(output_zip) as zf:
            zf.extractall(workspace / variant_id / "output" / output_id)

    res = client.put(f"/v1/studies/{v2_id}/archive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, admin_access_token, res.json())
    assert task.result is not None and task.result.success, task

    # The variant and its descendant are archived: their snapshot is removed, their outputs moved to an archive file
    for variant_id in (v2_id, v3_id):
        assert _is_archived(client, variant_id)
        assert not (workspace / variant_id).exists()
        with zipfile.ZipFile(archives / f"{variant_id}.zip") as zf:
            assert all(name.startswith(f"output/{output_id}/") for name in zf.namelist())

    # An archived variant can neither be read nor modified, which would generate its snapshot again
    for variant_id in (v2_id, v3_id):
        res = client.get(f"/v1/studies/{variant_id}/areas")
        assert res.status_code == 400, res.json()
        assert res.json()["exception"] == "UnsupportedOperationOnArchivedStudy"
        command = {"action": "create_area", "args": {"area_name": "other_area"}}
        res = client.put(f"/v1/studies/{variant_id}/commands", json=[command])
        assert res.status_code == 400, res.json()
        assert res.json()["exception"] == "UnsupportedOperationOnArchivedStudy"
        assert not (workspace / variant_id).exists()
        # Its commands can still be read
        assert len(client.get(f"/v1/studies/{variant_id}/commands").json()) == 1

    # The ancestors are left untouched
    assert not _is_archived(client, v1_id)
    assert (workspace / v1_id / "snapshot").is_dir()
    assert (workspace / v1_id / "output" / output_id).is_dir()

    # The disk usage of an archived variant can be computed
    res = client.get(f"/v1/studies/{v2_id}/disk-usage")
    assert res.status_code == 200, res.json()

    # Unarchiving a variant also unarchives its archived ancestors: their outputs are restored
    res = client.put(f"/v1/studies/{v3_id}/unarchive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, admin_access_token, res.json())
    assert task.result is not None and task.result.success, task
    for variant_id in (v2_id, v3_id):
        assert not _is_archived(client, variant_id)
        assert (workspace / variant_id / "output" / output_id / "about-the-study" / "parameters.ini").is_file()
        assert not (archives / f"{variant_id}.zip").exists()
    # Its snapshot is generated again when the study is read
    res = client.get(f"/v1/studies/{v3_id}/areas")
    assert res.status_code == 200, res.json()
    assert (workspace / v3_id / "snapshot").is_dir()

    # Deleting an archived variant removes its archive file
    res = client.put(f"/v1/studies/{v3_id}/archive")
    wait_task_completion(client, admin_access_token, res.json())
    assert (archives / f"{v3_id}.zip").is_file()
    res = client.delete(f"/v1/studies/{v3_id}")
    assert res.status_code == 200, res.json()
    assert not (archives / f"{v3_id}.zip").exists()


def test_archive_reference_study_and_its_variants(
    admin_client: TestClient, admin_access_token: str, tmp_path: Path, output_zip: Path
) -> None:
    client = admin_client
    raw_id = client.post("/v1/studies?name=raw").json()
    variant_id = _create_variant(client, raw_id, "variant")
    variant_dir = tmp_path / "internal_workspace" / variant_id
    variant_archive = tmp_path / "archive_dir" / f"{variant_id}.zip"
    with zipfile.ZipFile(output_zip) as zf:
        zf.extractall(variant_dir / "output" / "20201014-1427eco")

    # Archiving the reference study archives its variants: their outputs are moved to an archive file
    res = client.put(f"/v1/studies/{raw_id}/archive")
    wait_task_completion(client, admin_access_token, res.json())
    assert _is_archived(client, raw_id)
    assert _is_archived(client, variant_id)
    assert variant_archive.is_file() and not variant_dir.exists()

    # Unarchiving the reference study leaves its variants archived, with their outputs
    res = client.put(f"/v1/studies/{raw_id}/unarchive")
    wait_task_completion(client, admin_access_token, res.json())
    assert not _is_archived(client, raw_id)
    assert _is_archived(client, variant_id)
    assert variant_archive.is_file() and not variant_dir.exists()
