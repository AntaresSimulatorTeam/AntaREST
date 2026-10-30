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
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


@pytest.mark.parametrize("storage_type", ["in_study", "outside_study"], indirect=True)
def test_output_raw_files(
    client: TestClient,
    user_access_token: str,
    internal_study_id: str,
    storage_type: tuple[str, dict[str, str]],
) -> None:
    _, name_map = storage_type
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = name_map.get("20201014-1427eco", "20201014-1427eco")

    # Tree structure of the output files
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files")
    assert res.status_code == 200, res.json()
    tree = res.json()
    assert tree["files"] == [
        "annualSystemCost.txt",
        "checkIntegrity.txt",
        "info.antares-output",
        "simulation-comments.txt",
        "simulation.log",
    ]
    assert [d["name"] for d in tree["directories"]] == ["about-the-study", "economy", "ts-numbers"]
    about_the_study = tree["directories"][0]
    assert about_the_study == {
        "name": "about-the-study",
        "files": ["areas.txt", "comments.txt", "links.txt", "map", "parameters.ini", "study.ini"],
        "directories": [],
    }

    # Content of an output file
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "about-the-study/areas.txt"},
    )
    assert res.status_code == 200, res.json()
    assert res.content == b"DE\r\nES\r\nFR\r\nIT\r\n"
    assert res.headers["content-type"] == "application/octet-stream"
    assert res.headers["content-disposition"] == 'attachment; filename="areas.txt"'

    # Unknown file, directory, or file outside the output
    for path in ["unknown.txt", "about-the-study", "../../study.antares"]:
        res = client.get(
            f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
            params={"path": path},
        )
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputFileNotFound"

    # Unknown output
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/unknown/raw-files")
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputNotFound"
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/unknown/raw-files/content",
        params={"path": "about-the-study/areas.txt"},
    )
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputNotFound"

    # Archived output
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_id}/_archive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, user_access_token, res.json())
    assert task.status == TaskStatus.COMPLETED
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files")
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnArchivedOutput"
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "about-the-study/areas.txt"},
    )
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnArchivedOutput"
