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

import pytest
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
    client: TestClient, user_access_token: str, internal_study_id: str, gems_views_output_dir: Path, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Import an output containing GEMS views
    res = client.post(
        f"/v1/studies/{internal_study_id}/output", files={"output": _zip_directory(gems_views_output_dir)}
    )
    assert res.status_code == 202, res.json()
    output_id = res.json()

    res = client.get(f"/v1/studies/{internal_study_id}/outputs")
    assert res.status_code == 200, res.json()
    output_types = {output["id"]: output["outputType"] for output in res.json()}
    assert output_types[output_id] == "GEMS_VIEWS"
    assert output_types["20201014-1427eco"] == "LEGACY"

    url = f"/v1/studies/{internal_study_id}/outputs/{output_id}/gems-views"

    # Ensures asking for the views before they were materialized returns a HTTP 404 with a status `NOT_FOUND`
    res = client.get(url)
    assert res.json() == {"status": "NOT_FOUND", "task_id": None}
    assert res.status_code == 404
    # Materialize the views
    task_id = client.post(f"{url}/materialize").json()
    res = client.get(url)
    if res.status_code == 404:
        assert res.json() == {"status": "IN_PROGRESS", "task_id": task_id}
    else:
        assert res.status_code == 200
    # Wait for materializing to end
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED
    # Asks for the views. This time, it should succeed.
    res = client.get(url)
    assert res.status_code == 200, res.json()
    assert res.json() == [
        {
            "taxonomy": "balance",
            "viewIds": {
                "view_area": {
                    "metricsLocation": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}],
                    "aggregationPatterns": [
                        {"id": "annual_all_scenario", "scenario": True, "timeGranularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "timeGranularity": "hour"},
                    ],
                },
                "view_storage": {
                    "metricsLocation": [{"id": "area3_node"}],
                    "aggregationPatterns": [
                        {"id": "annual_all_scenario", "scenario": True, "timeGranularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "timeGranularity": "hour"},
                    ],
                },
                "view_thermal": {
                    "metricsLocation": [{"id": "area1_node"}, {"id": "area2_node"}, {"id": "area3_node"}],
                    "aggregationPatterns": [
                        {"id": "annual_all_scenario", "scenario": True, "timeGranularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "timeGranularity": "hour"},
                    ],
                },
            },
        },
        {
            "taxonomy": "link",
            "viewIds": {
                "view_link": {
                    "metricsLocation": [
                        {"id": "area1_area2_link"},
                        {"id": "area1_area3_link"},
                        {"id": "area2_area3_link"},
                    ],
                    "aggregationPatterns": [
                        {"id": "annual_all_scenario", "scenario": True, "timeGranularity": "year"},
                        {"id": "hourly_per_scenario", "scenario": False, "timeGranularity": "hour"},
                    ],
                },
            },
        },
    ]

    # Once computed, the views do not depend on the parquet files anymore
    expected_views = res.json()
    parquet_files = list((tmp_path / "ext_workspace/STA-mini/output" / output_id / "views/output").glob("*.parquet"))
    assert len(parquet_files) == 8
    for parquet_file in parquet_files:
        parquet_file.unlink()
    res = client.get(url)
    assert res.status_code == 200, res.json()
    assert res.json() == expected_views

    # Try to materialize even if the views are already in the database. Should raise an exception
    res = client.post(f"{url}/materialize")
    assert res.status_code == 417, res.json()
    assert res.json() == {
        "description": "The output GEMS views are already materialized in DB",
        "exception": "HTTPException",
    }

    # Legacy output
    legacy_url = f"/v1/studies/{internal_study_id}/outputs/20201014-1427eco/gems-views"
    for res in (client.get(legacy_url), client.post(f"{legacy_url}/materialize")):
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "OutputGemsViewsNotFound"

    # Archived output
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_id}/_archive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, user_access_token, res.json())
    assert task.status == TaskStatus.COMPLETED
    for res in (client.get(url), client.post(f"{url}/materialize")):
        assert res.status_code == 400, res.json()
        assert res.json()["exception"] == "UnsupportedOperationOnArchivedOutput"


@pytest.mark.parametrize("output_storage", ["IN_STUDY_FILE_TREE", "OUT_OF_STUDY_FILE_TREE"])
def test_output_gems_view_matrix(
    client: TestClient,
    user_access_token: str,
    internal_study_id: str,
    gems_views_output_dir: Path,
    output_storage: str,
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    res = client.post(
        f"/v1/studies/{internal_study_id}/output",
        files={"output": _zip_directory(gems_views_output_dir)},
        params={"storage_type": output_storage},
    )
    assert res.status_code == 202, res.json()
    output_id = res.json()
    outputs = client.get(f"/v1/studies/{internal_study_id}/outputs").json()
    assert next(output for output in outputs if output["id"] == output_id)["storageType"] == output_storage
    views_url = f"/v1/studies/{internal_study_id}/outputs/{output_id}/gems-views"
    matrix_url = f"{views_url}/view_storage/matrix"
    synthesis = {"time_granularity": "year", "metric_location": "area3_node"}
    year_2 = {"time_granularity": "hour", "metric_location": "area3_node", "mc_year": 2}

    # The matrix needs the views to be materialized
    res = client.get(matrix_url, params=synthesis)
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "GemsViewsNotMaterialized"
    task = wait_task_completion(client, user_access_token, client.post(f"{views_url}/materialize").json())
    assert task.status == TaskStatus.COMPLETED

    # Statistics (values checked by the unit tests)
    res = client.get(matrix_url, params=synthesis)
    assert res.status_code == 200, res.json()
    matrix = res.json()
    assert matrix["index"] == {"startDate": "2026-01-01T00:00:00", "steps": 1, "timeGranularity": "year", "stepSize": 1}
    assert matrix["columns"][0] == ["area3_short_term_storage_st / CASHFLOW", "", "exp"]
    assert len(matrix["columns"]) == len(matrix["data"][0]) == 16
    assert matrix["data"][0][0] == 5145405.5

    # One Monte Carlo year
    res = client.get(matrix_url, params=year_2)
    assert res.status_code == 200, res.json()
    matrix = res.json()
    assert matrix["index"] == {"startDate": "2026-01-01T00:00:00", "steps": 3, "timeGranularity": "hour", "stepSize": 1}
    assert matrix["columns"][0] == ["area3_short_term_storage_st / CASHFLOW", "", ""]
    # 686.0 in year 1
    assert matrix["data"][0][0] == 35.0

    # Year not simulated
    res = client.get(matrix_url, params={**year_2, "mc_year": 3})
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "GemsViewMatrixNotFound"

    # No aggregation pattern with this time granularity in the view
    res = client.get(matrix_url, params={**synthesis, "time_granularity": "day"})
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "GemsViewMatrixNotFound"

    # A Monte Carlo year selects the `scenario: false` pattern: none at year granularity
    res = client.get(matrix_url, params={**synthesis, "mc_year": 1})
    assert res.status_code == 404, res.json()
    assert res.json()["description"] == (
        "Aggregation pattern with time granularity 'year' and scenario 'false' not found in view 'view_storage'"
    )

    # Location not in the view: only `area3_node` has a storage
    res = client.get(matrix_url, params={**synthesis, "metric_location": "area1_node"})
    assert res.status_code == 404, res.json()
    assert res.json()["description"] == "Location 'area1_node' not found in view 'view_storage'"

    # Legacy output
    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/20201014-1427eco/gems-views/view_storage/matrix", params=synthesis
    )
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputGemsViewsNotFound"

    # Archived output
    res = client.post(f"/v1/studies/{internal_study_id}/outputs/{output_id}/_archive")
    assert res.status_code == 200, res.json()
    task = wait_task_completion(client, user_access_token, res.json())
    assert task.status == TaskStatus.COMPLETED
    res = client.get(matrix_url, params=synthesis)
    assert res.status_code == 400, res.json()
    assert res.json()["exception"] == "UnsupportedOperationOnArchivedOutput"


@pytest.mark.parametrize("storage_type", ["v2"], indirect=True)
def test_output_gems_view_matrix_v2(
    client: TestClient, user_access_token: str, internal_study_id: str, storage_type: dict[str, str]
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = storage_type["20201014-1427eco"]

    res = client.get(
        f"/v1/studies/{internal_study_id}/outputs/{output_id}/gems-views/view_storage/matrix",
        params={"time_granularity": "year", "metric_location": "area3_node"},
    )
    assert res.status_code == 404, res.json()
    assert res.json()["exception"] == "OutputGemsViewsNotFound"
