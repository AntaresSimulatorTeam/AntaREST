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
import zipfile
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


def _zip_directory(directory: Path) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path in directory.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(directory).as_posix())
    buffer.seek(0)
    return buffer


def test_output_gems_views(
    client: TestClient, user_access_token: str, internal_study_id: str, project_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Import an output containing GEMS views
    gems_output_dir = project_path / "tests/output/filestudy/data/20261104-1636eco-gems_views"
    res = client.post(f"/v1/studies/{internal_study_id}/output", files={"output": _zip_directory(gems_output_dir)})
    assert res.status_code == 202, res.json()
    output_id = res.json()

    # Nominal case
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/gems-views")
    assert res.status_code == 200, res.json()
    assert res.json() == [
        {
            "taxonomy": "balance",
            "viewIds": [
                {
                    "view_area": {
                        "metricsLocation": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}]
                    },
                    "view_storage": {"metricsLocation": [{"id": "area3_node"}]},
                    "view_thermal": {
                        "metricsLocation": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}]
                    },
                }
            ],
        },
        {
            "taxonomy": "link",
            "viewIds": [
                {
                    "view_link": {
                        "metricsLocation": [
                            {"id": "area1_area2_link"},
                            {"id": "area1_area3_link"},
                            {"id": "area2_area3_link"},
                        ]
                    }
                }
            ],
        },
    ]

    # Legacy output
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/20201014-1427eco/gems-views")
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputGemsViewsNotFound"

    # Archived output
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_id}/_archive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, user_access_token, res.json())
    assert task.status == TaskStatus.COMPLETED
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/gems-views")
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnArchivedOutput"
