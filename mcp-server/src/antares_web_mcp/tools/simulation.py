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

"""Tools to run simulations: launchers, jobs, progress and logs."""

import re
import time
from typing import Annotated, Any, Literal

import anyio
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.common import (
    ADDITIVE,
    DESTRUCTIVE,
    READ_ONLY,
    JobId,
    StudyId,
    guard,
    parse_version,
    without_none,
)

FINAL_JOB_STATUSES = {"success", "failed"}
POLL_INTERVAL_SECONDS = 5.0
ERROR_MARKERS = ("error", "fatal", "exception", "abort")
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")  # colour codes of the solver logs


class Launcher(BaseModel):
    id: str = Field(description="Launcher id, to pass to `launch_study`.")
    name: str
    solver_versions: list[str] = Field(description="Antares Simulator versions this launcher can run.")
    nb_cores: dict[str, int] = Field(default={}, description="Allowed number of CPU cores (min, max, default).")


class LaunchersInfo(BaseModel):
    default_launcher: str
    launchers: list[Launcher]


class LaunchResult(BaseModel):
    job_id: str
    launcher: str
    solver_version: str
    study_version: str


class JobInfo(BaseModel):
    id: str
    study_id: str
    status: str = Field(description="'pending', 'running', 'success' or 'failed'.")
    output_id: str | None = Field(default=None, description="Id of the produced output, once the job succeeded.")
    exit_code: int | None = None
    message: str | None = None
    launcher: str | None = None
    created: str | None = None
    completed: str | None = None
    progress: float | None = Field(default=None, description="Progress in percent, while the job is running.")

    @classmethod
    def from_api(cls, data: dict[str, Any], *, progress: float | None = None) -> "JobInfo":
        return cls(
            id=data["id"],
            study_id=data["study_id"],
            status=data["status"],
            output_id=data.get("output_id"),
            exit_code=data.get("exit_code"),
            message=data.get("msg") or None,
            launcher=data.get("launcher"),
            created=data.get("creation_date"),
            completed=data.get("completion_date"),
            progress=progress,
        )


class WaitResult(BaseModel):
    finished: bool = Field(description="False if the timeout was reached before the end of the job.")
    waited_seconds: int
    job: JobInfo


def register(mcp: MCPServer, client: AntaresWebClient, *, read_only: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_launchers() -> LaunchersInfo:
        """
        List the launchers configured on Antares Web (local machine, SLURM cluster, ...) with the
        Antares Simulator versions they can run and their CPU limits.
        """
        data = await guard(client.list_launchers())
        return LaunchersInfo(
            default_launcher=data.get("defaultLauncher", ""),
            launchers=[
                Launcher(
                    id=launcher["id"],
                    name=launcher.get("name", launcher["id"]),
                    solver_versions=launcher.get("versions", []),
                    nb_cores=launcher.get("nbCores") or {},
                )
                for launcher in data.get("launchers", [])
            ],
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_job(job_id: JobId) -> JobInfo:
        """Get the status of a simulation job (and its output id once it succeeded)."""
        return await _job_info(client, job_id)

    @mcp.tool(annotations=READ_ONLY)
    async def list_jobs(
        study_id: Annotated[str | None, Field(description="Only the jobs of this study.")] = None,
        latest: Annotated[int, Field(ge=1, le=100, description="Maximum number of jobs, most recent first.")] = 10,
    ) -> list[JobInfo]:
        """List the most recent simulation jobs, optionally for one study."""
        jobs = await guard(client.list_jobs(study_id=study_id, latest=latest))
        jobs.sort(key=lambda job: job.get("creation_date") or "", reverse=True)
        return [JobInfo.from_api(job) for job in jobs[:latest]]

    @mcp.tool(annotations=READ_ONLY)
    async def wait_for_job(
        job_id: JobId,
        ctx: Context[Any, Any],
        timeout_seconds: Annotated[int, Field(ge=10, le=1800, description="Maximum time to wait, in seconds.")] = 600,
    ) -> WaitResult:
        """
        Wait until a simulation job is finished (success or failure), reporting its progress.
        If the timeout is reached, returns `finished: false`: call it again to keep waiting.
        When a job failed, call `get_job_logs` to understand why.
        """
        start = _now()
        while True:
            job = await _job_info(client, job_id)
            waited = int(_now() - start)
            if job.status in FINAL_JOB_STATUSES:
                await ctx.report_progress(100, 100, f"Job {job.status}")
                return WaitResult(finished=True, waited_seconds=waited, job=job)
            if waited >= timeout_seconds:
                return WaitResult(finished=False, waited_seconds=waited, job=job)
            await ctx.report_progress(job.progress or 0, 100, f"Job {job.status}")
            await anyio.sleep(min(POLL_INTERVAL_SECONDS, max(timeout_seconds - waited, 1)))

    @mcp.tool(annotations=READ_ONLY)
    async def get_job_logs(
        job_id: JobId,
        stream: Annotated[
            Literal["both", "stdout", "stderr"],
            Field(description="Solver output stream. Errors are usually in 'stderr'."),
        ] = "both",
        tail_lines: Annotated[int, Field(ge=1, le=2000, description="Number of last lines of each stream.")] = 60,
        errors_only: Annotated[
            bool, Field(description="Only keep the lines mentioning an error, fatal error or exception.")
        ] = False,
    ) -> dict[str, str]:
        """Get the last lines of the solver logs of a job, typically to understand why a simulation failed."""
        streams = ["STDOUT", "STDERR"] if stream == "both" else [stream.upper()]
        logs: dict[str, str] = {}
        for log_type in streams:
            lines = ANSI_ESCAPE.sub("", await guard(client.get_job_logs(job_id, log_type=log_type))).splitlines()
            if errors_only:
                lines = [line for line in lines if any(marker in line.lower() for marker in ERROR_MARKERS)]
            logs[log_type.lower()] = "\n".join(lines[-tail_lines:])
        return logs

    if read_only:
        return

    @mcp.tool(annotations=ADDITIVE)
    async def launch_study(
        study_id: StudyId,
        launcher: Annotated[
            str | None, Field(description="Launcher id (see `list_launchers`). Default: the default launcher.")
        ] = None,
        solver_version: Annotated[
            str | None,
            Field(
                description=(
                    "Antares Simulator version, e.g. '8.8'. Default: the study version if the launcher "
                    "supports it, otherwise the closest higher version it supports."
                )
            ),
        ] = None,
        nb_cpu: Annotated[int | None, Field(ge=1, description="Number of CPU cores.")] = None,
        output_suffix: Annotated[
            str | None, Field(pattern=r"^[^/\\=]*$", description="Suffix appended to the output name.")
        ] = None,
        time_limit_hours: Annotated[
            int | None, Field(ge=1, description="Maximum duration of the job, in hours.")
        ] = None,
    ) -> LaunchResult:
        """
        Launch a simulation of a study. Returns immediately with a job id: then call `wait_for_job`.
        The simulation uses the study settings (see `get_simulation_settings`).
        """
        launchers = await guard(client.list_launchers())
        launcher_id = launcher or launchers.get("defaultLauncher")
        known = {item["id"]: item for item in launchers.get("launchers", [])}
        if launcher_id not in known:
            raise ToolError(f"Unknown launcher '{launcher_id}'. Available launchers: {sorted(known)}.")
        study_version = str((await guard(client.get_study(study_id)))["version"])
        version = solver_version or choose_solver_version(study_version, known[launcher_id].get("versions", []))

        parameters = without_none(
            {
                "nb_cpu": nb_cpu,
                "output_suffix": output_suffix,
                "time_limit": time_limit_hours * 3600 if time_limit_hours else None,
            }
        )
        job_id = await guard(
            client.launch_study(study_id, launcher=launcher_id, solver_version=version, parameters=parameters)
        )
        return LaunchResult(job_id=job_id, launcher=launcher_id, solver_version=version, study_version=study_version)

    @mcp.tool(annotations=DESTRUCTIVE)
    async def kill_job(job_id: JobId) -> str:
        """Stop a pending or running simulation job. Its partial results are lost."""
        await guard(client.kill_job(job_id))
        return f"Job {job_id} killed."


def _now() -> float:
    """Monotonic clock (a function, so that tests can replace it without touching the event loop clock)."""
    return time.monotonic()


async def _job_info(client: AntaresWebClient, job_id: str) -> JobInfo:
    job = await guard(client.get_job(job_id))
    progress = await guard(client.get_job_progress(job_id)) if job.get("status") == "running" else None
    return JobInfo.from_api(job, progress=progress)


def choose_solver_version(study_version: str, available: list[str]) -> str:
    """
    Chooses the solver version to run a study: the study version itself if available,
    otherwise the closest higher available version (Antares Simulator reads older studies).
    """
    target = parse_version(study_version)
    candidates = sorted((v for v in available if parse_version(v) >= target), key=parse_version)
    if not candidates:
        raise ToolError(
            f"No solver can run this study (version {study_version}): the launcher supports {available}. "
            "Use another launcher, or a study in a supported version."
        )
    return candidates[0]
