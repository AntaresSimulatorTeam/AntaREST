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

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.assets import ASSETS_DIR as INTEGRATION_ASSETS_DIR
from tests.integration.prepare_proxy import PreparerProxy
from tests.integration.utils import wait_task_completion
from tests.test_helpers.dates import utc_to_local


@pytest.mark.parametrize("storage_type", ["in_study", "outside_study"], indirect=True)
def test_output_raw_files(
    client: TestClient,
    user_access_token: str,
    internal_study_id: str,
    storage_type: tuple[str, dict[str, str]],
) -> None:
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
    assert res.headers["content-disposition"] == 'attachment; filename="areas.txt"'

    # Unknown file, directory, or file outside the output
    for path in ["unknown.txt", "about-the-study", "../../study.antares"]:
        res = client.get(
            f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
            params={"path": path},
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

    # Output ids that are not a direct child of the study outputs folder
    for output_id_outside in ["%2E%2E", "%2E"]:
        res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id_outside}/raw-files")
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputNotFound"
        res = client.get(
            f"/v1/studies/{internal_study_id}/outputs/{output_id_outside}/raw-files/content",
            params={"path": "study.antares"},
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


@pytest.mark.parametrize("storage_type", ["v2"], indirect=True)
def test_output_raw_files_unsupported_for_v2(
    client: TestClient,
    user_access_token: str,
    internal_study_id: str,
    storage_type: tuple[str, dict[str, str]],
) -> None:
    _, name_map = storage_type
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = name_map["20201014-1427eco"]

    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files")
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnOutputStorage"
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "about-the-study/areas.txt"},
    )
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnOutputStorage"


def test_output_raw_files_database_study(client: TestClient, user_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    preparer = PreparerProxy(client, user_access_token)
    study_id = preparer.create_study("db-study", storage_mode="database")

    # Outputs of database studies are stored outside the study
    output = io.BytesIO((INTEGRATION_ASSETS_DIR / "output_adq.7z").read_bytes())
    res = client.post(f"/v1/studies/{study_id}/output", files={"output": output})
    assert res.status_code == 202, res.json()
    output_id = f"{utc_to_local('20221003-2142')}adq"

    res = client.get(f"/v1/studies/{study_id}/outputs/{output_id}/raw-files")
    assert res.status_code == 200, res.json()
    tree = res.json()
    assert "simulation.log" in tree["files"]
    assert "about-the-study" in [d["name"] for d in tree["directories"]]

    res = client.get(
        f"/v1/studies/{study_id}/outputs/{output_id}/raw-files/content",
        params={"path": "about-the-study/areas.txt"},
    )
    assert res.status_code == 200, res.json()
    assert res.content == b"DE\r\nES\r\nFR\r\nIT\r\n"
