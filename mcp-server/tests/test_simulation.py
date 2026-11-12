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

from typing import Any

import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import create_server
from antares_web_mcp.tools import simulation
from antares_web_mcp.tools.simulation import choose_solver_version
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data, error_text

JOB_ID = "66a81f22-e1e5-482f-a504-49ae660e5ece"
LAUNCHERS = {
    "defaultLauncher": "local_id",
    "launchers": [
        {"id": "local_id", "name": "my_local", "versions": ["8.8", "10.2"], "nbCores": {"min": 1, "max": 12}},
        {"id": "slurm", "name": "cluster", "versions": ["8.8"]},
    ],
}


def job(status: str, **extra: Any) -> dict[str, Any]:
    return {"id": JOB_ID, "study_id": STUDY_ID, "status": status, "creation_date": "2026-11-07", **extra}


@pytest.mark.parametrize(
    "study_version, available, expected",
    [
        ("8.8", ["8.6", "8.8", "10.2"], "8.8"),  # exact match
        ("9.2", ["8.8", "10.2", "9.3"], "9.3"),  # closest higher version
        ("8.8", ["10.2", "9.2"], "9.2"),
        ("880", ["8.8", "10.2"], "8.8"),  # legacy version format
    ],
)
def test_choose_solver_version(study_version: str, available: list[str], expected: str) -> None:
    assert choose_solver_version(study_version, available) == expected


def test_choose_solver_version_without_compatible_solver() -> None:
    with pytest.raises(ToolError, match="No solver can run this study"):
        choose_solver_version("10.2", ["8.8"])


@pytest.mark.anyio
async def test_launch_study_picks_a_compatible_solver(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", "/v1/launcher/launchers", json_body=LAUNCHERS)
    fake_api.route("GET", f"/v1/studies/{STUDY_ID}", json_body={"id": STUDY_ID, "version": "9.2"})
    fake_api.route("POST", f"/v1/launcher/run/{STUDY_ID}", json_body={"job_id": JOB_ID})

    result = await call(api_client, "launch_study", {"study_id": STUDY_ID, "nb_cpu": 4, "time_limit_hours": 2})

    assert data(result) == {"job_id": JOB_ID, "launcher": "local_id", "solver_version": "10.2", "study_version": "9.2"}
    request = fake_api.requests_to("POST", f"/v1/launcher/run/{STUDY_ID}")[0]
    assert (request.url.params["launcher"], request.url.params["version"]) == ("local_id", "10.2")
    assert fake_api.json_sent_to("POST", f"/v1/launcher/run/{STUDY_ID}") == [{"nb_cpu": 4, "time_limit": 7200}]


@pytest.mark.anyio
async def test_launch_study_with_unknown_launcher(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    fake_api.route("GET", "/v1/launcher/launchers", json_body=LAUNCHERS)

    result = await call(api_client, "launch_study", {"study_id": STUDY_ID, "launcher": "nope"})

    assert "Available launchers: ['local_id', 'slurm']" in error_text(result)


@pytest.mark.anyio
async def test_wait_for_job_reports_progress(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(simulation, "POLL_INTERVAL_SECONDS", 0.01)
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job("pending"))
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job("running"))
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job("success", output_id="20261107-1121eco"))
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}/progress", json_body=42)
    reported: list[float] = []

    async def on_progress(progress: float, total: float | None, message: str | None) -> None:
        reported.append(progress)

    async with Client(create_server(api_client)) as client:
        result = await client.call_tool("wait_for_job", {"job_id": JOB_ID}, progress_callback=on_progress)

    waited = data(result)
    assert waited["finished"] is True
    assert waited["job"]["output_id"] == "20261107-1121eco"
    assert reported == [0, 42, 100]


@pytest.mark.anyio
async def test_wait_for_job_timeout(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(simulation, "POLL_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(simulation, "_now", iter(range(0, 1000, 20)).__next__)
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job("pending"))

    result = await call(api_client, "wait_for_job", {"job_id": JOB_ID, "timeout_seconds": 30})

    assert data(result)["finished"] is False


@pytest.mark.anyio
async def test_get_job_logs_strips_colours_and_filters_errors(
    fake_api: FakeAntaresWeb, api_client: AntaresWebClient
) -> None:
    logs = "\n".join(
        [
            "[solver][infos] Loading the area fr",
            "[solver]\x1b[0;31m[error]\x1b[0m fr: Invalid reservoir capacity.",
            "[solver]\x1b[0;31m[fatal]\x1b[0m The simulation must stop.",
        ]
    )
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}/logs", json_body=logs)

    result = await call(api_client, "get_job_logs", {"job_id": JOB_ID, "stream": "stderr", "errors_only": True})

    assert data(result) == {
        "stderr": "[solver][error] fr: Invalid reservoir capacity.\n[solver][fatal] The simulation must stop."
    }
    assert fake_api.last_request.url.params["log_type"] == "STDERR"
