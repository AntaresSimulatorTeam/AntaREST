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
import shutil
import zipfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.core.utils.archives import ArchiveFormat, archive_dir


@pytest.fixture
def empty_output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    """
    Just a duplicate of output "20201014-1430adq" with no mc-all data
    """
    unzip_path = tmp_path / "empty-output"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zip_file:
        zip_file.extractall(unzip_path, members=[f for f in zip_file.namelist() if "20201014-1430adq" in f])

    output_path = unzip_path / "STA-mini" / "output" / "20201014-1430adq"
    shutil.rmtree(output_path / "adequacy" / "mc-all")

    output_zip_path = tmp_path / "empty-output.zip"
    archive_dir(
        src_dir_path=output_path,
        target_archive_path=output_zip_path,
        remove_source_dir=True,
        archive_format=ArchiveFormat.ZIP,
    )
    return output_zip_path


def test_get_digest_endpoint(
    client: TestClient, user_access_token: str, internal_study_id: str, empty_output_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Nominal case
    output_id = "20201014-1422eco-hello"
    res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{output_id}/digest-ui")
    assert res.status_code == 200
    digest = res.json()
    assert list(digest.keys()) == ["area", "districts", "flowLinear", "flowQuadratic"]
    assert digest["districts"] == {"columns": [], "data": [], "groupedColumns": False}
    flow = {
        "columns": ["", "de", "es", "fr", "it"],
        "data": [
            ["de", "X", "--", "0", "--"],
            ["es", "--", "X", "0", "--"],
            ["fr", "0", "0", "X", "0"],
            ["it", "--", "--", "0", "X"],
        ],
        "groupedColumns": False,
    }
    assert digest["flowQuadratic"] == flow
    assert digest["flowLinear"] == flow
    area_matrix = digest["area"]
    assert area_matrix["groupedColumns"] is True
    assert area_matrix["columns"][:3] == [[""], ["OV. COST", "Euro", "EXP"], ["OP. COST", "Euro", "EXP"]]

    # Asserts we have a 404 Exception when the output doesn't exist
    res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/fake_output/digest-ui")
    assert res.status_code == 404
    assert res.json() == {
        "description": "Output 'fake_output' not found",
        "exception": "OutputNotFound",
    }

    # Asserts we can read digest also in "adequacy" outputs
    adequacy_output = "20201014-1430adq"
    res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{adequacy_output}/digest-ui")
    assert res.status_code == 200
    digest = res.json()
    assert list(digest.keys()) == ["area", "districts", "flowLinear", "flowQuadratic"]

    # Replace the last output with an output without mc-all data
    res = client.delete(f"/v1/studies/{internal_study_id}/outputs/{adequacy_output}")
    assert res.status_code == 200
    # Ensures the output has been successfully deleted
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert len(res.json()) == 5

    res = client.post(
        f"/v1/studies/{internal_study_id}/output", files={"output": io.BytesIO(empty_output_path.read_bytes())}
    )
    assert res.status_code == 202
    output_id = res.json()
    # Ensures the output has been successfully imported
    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert len(res.json()) == 6

    res = client.get(f"/v1/private/studies/{internal_study_id}/outputs/{output_id}/digest-ui")
    assert res.status_code == 404
    assert res.json()["exception"] == "OutputSubFolderNotFound"
