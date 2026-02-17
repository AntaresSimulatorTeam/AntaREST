# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from integration.assets import ASSETS_DIR
from starlette.testclient import TestClient


def test_import(admin_client: TestClient, internal_study_id: str, tmp_path: Path) -> None:
    client = admin_client

    # Import an output and store it with new storage type
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    res = client.post(
        f"/v1/studies/{internal_study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    assert res.json() == "20221004-1430adq"

    # Check output metadata
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs",
    )
    assert len(res.json()) == 7
    assert res.json()[-1] == {
        "archived": False,
        "completionDate": "",
        "name": "20221004-1430adq",
        "settings": {
            "advancedParameters": {},
            "general": {},
            "input": {},
            "optimization": {},
            "otherPreferences": {},
            "output": {},
            "playlist": None,
            "seedsMersenneTwister": {},
        },
        "status": "",
        "type": "Adequacy",
    }


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
    output_path_zip = ASSETS_DIR / "output_adq.zip"
    res = client.post(
        f"/v1/studies/{study_id}/output?storage_type=V2",
        files={"output": io.BytesIO(output_path_zip.read_bytes())},
    )
    assert res.status_code == 202, res.json()
    assert res.json() == "20221004-1430adq"

    # Check output metadata
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert len(res.json()) == 1

    # Delete study
    res = client.delete(f"/v1/studies/{study_id}")
    assert res.status_code == 200
