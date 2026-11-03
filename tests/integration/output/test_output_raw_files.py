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
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


@pytest.mark.parametrize("storage_type", ["in_study", "outside_study"], indirect=True)
@pytest.mark.usefixtures("storage_type")
def test_output_raw_files(client: TestClient, user_access_token: str, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = "20201014-1427eco"

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

    # Unknown file (other cases are covered at storage level)
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "unknown.txt"},
    )
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputFileNotFound"

    # Path containing a new line, which could forge log entries
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "areas.txt\nINFO forged log entry"},
    )
    assert res.status_code == 422, res.json()

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


@pytest.mark.parametrize("storage_type", ["in_study", "outside_study"], indirect=True)
@pytest.mark.usefixtures("storage_type")
def test_output_raw_files_path_traversal(
    client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
) -> None:
    """
    At endpoint level, `SanitizedStr` only rejects line breaks: output ids like ".." and paths like "../x"
    are accepted, so the storage must prevent them from escaping the output folder.
    """
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = "20201014-1427eco"
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("secret")

    absolute_path = secret_file.as_posix()
    # Climbs up to the filesystem root (extra ".." are ignored there), then down to the secret file
    dot_dot_path = "../" * (len(tmp_path.parts) + 5) + secret_file.relative_to(secret_file.anchor).as_posix()
    for path in [absolute_path, dot_dot_path]:
        res = client.get(
            f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content", params={"path": path}
        )
        assert res.status_code == 404, (path, res.content)
        assert res.json()["exception"] == "OutputFileNotFound"

    # Output ids that are not a direct child of the outputs folder
    for output_id_outside in ["%2E%2E", "%2E%2E%5C", "%2E"]:
        res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id_outside}/raw-files")
        assert res.status_code == 404, res.content
        assert res.json()["exception"] == "OutputNotFound"
        res = client.get(
            f"/v1/studies/{internal_study_id}/outputs/{output_id_outside}/raw-files/content",
            params={"path": f"{output_id}/info.antares-output"},
        )
        assert res.status_code == 404, res.content
        assert res.json()["exception"] == "OutputNotFound"
