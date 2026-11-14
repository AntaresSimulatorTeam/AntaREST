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

"""
Diagnosis of a failed simulation (`diagnose_job`).

The tool gathers what Antares Web knows about a job (status, exit code, duration, logs, study
version, solver versions of the launcher) and matches it against known failure patterns. Like
`check_study`, the rules are deterministic and unit tested: the same job always gives the same
probable causes, and the model then explains them and digs further if needed.

The patterns are heuristics on the solver logs: a cause is *probable*, with a confidence level
and the evidence it relies on, never a certainty.
"""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient, AntaresWebError
from antares_web_mcp.tools.common import READ_ONLY, JobId, guard, parse_version
from antares_web_mcp.tools.simulation import ANSI_ESCAPE, JobInfo

Confidence = Literal["high", "medium", "low"]
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}
MAX_EVIDENCE_LINES = 5
MAX_ERROR_LINES = 30
MAX_LAST_LINES = 20
MAX_LINE_LENGTH = 400
# A log line reporting a problem: a solver tag ([error], [fatal]) or a whole word. Whole words only:
# the licence banner printed by the solver mentions "exceptions".
ERROR_LINE = re.compile(r"\[(error|fatal|critical)\]|\b(error|fatal|exception|abort(ed|ing)?)\b", re.IGNORECASE)
# Informative lines of the solver are never errors, even when they mention one ("behavior: error-verbose").
INFO_LINE = re.compile(r"\[(infos?|notic|notice|check|debug|progress)\]", re.IGNORECASE)
# Lines written by Antares Web itself before the solver starts.
PREPARATION_LINES = re.compile(r"^(extracting study|study extracted)", re.IGNORECASE)


class Cause(BaseModel):
    code: str = Field(description="Stable identifier of the failure pattern.")
    confidence: Confidence
    title: str
    explanation: str = Field(description="What probably happened.")
    suggestion: str = Field(description="What the user can do.")
    evidence: list[str] = Field(description="Log lines or facts the cause relies on.")


class JobDiagnosis(BaseModel):
    job: JobInfo
    study_name: str | None = None
    study_version: str | None = None
    duration_seconds: int | None = Field(default=None, description="Time between the creation and the end of the job.")
    launcher_solver_versions: list[str] = Field(description="Solver versions the launcher of the job can run.")
    causes: list[Cause] = Field(description="Probable causes of the failure, most likely first.")
    error_lines: list[str] = Field(description=f"Last log lines mentioning an error (at most {MAX_ERROR_LINES}).")
    last_lines: list[str] = Field(description=f"Last lines of the solver output (at most {MAX_LAST_LINES}).")
    notes: list[str]


@dataclass
class JobFacts:
    """Everything the rules need, gathered once."""

    job: JobInfo
    stdout: list[str]
    stderr: list[str]
    study_version: str | None
    launcher_versions: list[str]
    duration_seconds: int | None

    @property
    def solver_lines(self) -> list[str]:
        """Lines written by the solver (the preparation lines of Antares Web are left out)."""
        return [line for line in [*self.stdout, *self.stderr] if not PREPARATION_LINES.match(line.strip())]

    def matching(self, pattern: str) -> list[str]:
        regex = re.compile(pattern, re.IGNORECASE)
        return [line for line in self.solver_lines if regex.search(line)][-MAX_EVIDENCE_LINES:]


def is_error_line(line: str) -> bool:
    return bool(ERROR_LINE.search(line)) and not INFO_LINE.search(line)


def clean_lines(text: str) -> list[str]:
    lines = (ANSI_ESCAPE.sub("", line).rstrip()[:MAX_LINE_LENGTH] for line in text.splitlines())
    return [line for line in lines if line.strip()]


def duration_between(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        return int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
    except ValueError:
        return None


def format_duration(seconds: int) -> str:
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    parts = [(days, "d"), (hours, "h"), (minutes, "min"), (secs, "s")]
    return " ".join(f"{value} {unit}" for value, unit in parts if value) or "0 s"


# ----------------------------------------------------------------------
# Rules
# ----------------------------------------------------------------------


def no_solver_output(facts: JobFacts) -> Cause | None:
    """The solver wrote nothing: the failure is on the server side, not in the study."""
    if facts.solver_lines:
        return None
    evidence = ["The logs contain no line written by the solver."]
    if facts.duration_seconds is not None:
        evidence.append(f"The job lasted {format_duration(facts.duration_seconds)}.")
    if facts.job.exit_code is None:
        evidence.append("The job has no exit code: the solver did not end by itself.")
        return Cause(
            code="solver_not_started",
            confidence="high",
            title="The solver never ran",
            explanation=(
                "The study was prepared, but the solver process never started or was lost before writing "
                "anything (for instance the server or the launcher was restarted). The job was then marked as "
                "failed, by a stop request or by the server. The study data is not the cause."
            ),
            suggestion=(
                "Launch the simulation again. If it fails the same way, report it to the administrator of "
                "Antares Web, with the job id."
            ),
            evidence=evidence,
        )
    evidence.append(f"Exit code of the solver: {facts.job.exit_code}.")
    return Cause(
        code="solver_crashed_at_start",
        confidence="medium",
        title="The solver stopped without any output",
        explanation=(
            "The solver process ended immediately with an error code and wrote nothing: the solver binary "
            "probably cannot run on the launcher (missing or incompatible binary, missing library)."
        ),
        suggestion="Report it to the administrator of Antares Web, with the job id and the launcher.",
        evidence=evidence,
    )


def unreadable_study(facts: JobFacts) -> Cause | None:
    lines = facts.matching(r"not seem to be a valid study|invalid study|unsupported (study )?version")
    if not lines:
        return None
    versions = f" The launcher can run: {', '.join(facts.launcher_versions)}." if facts.launcher_versions else ""
    return Cause(
        code="solver_version_mismatch",
        confidence="high",
        title="The solver cannot read this study version",
        explanation=(
            f"The solver rejected the study as invalid. This happens when the solver version is older than the "
            f"study version ({facts.study_version or 'unknown'}).{versions}"
        ),
        suggestion="Launch again with a solver version equal to or higher than the study version.",
        evidence=lines,
    )


def no_compatible_solver(facts: JobFacts) -> Cause | None:
    if not facts.study_version or not facts.launcher_versions:
        return None
    try:
        study = parse_version(facts.study_version)
        newest = max(parse_version(version) for version in facts.launcher_versions)
    except ValueError:
        return None
    if study <= newest:
        return None
    return Cause(
        code="no_compatible_solver",
        confidence="medium",
        title="The launcher has no solver for this study version",
        explanation=(
            f"The study is in version {facts.study_version}, but the most recent solver of the launcher is "
            f"{'.'.join(str(part) for part in newest)}: an older solver cannot read a newer study."
        ),
        suggestion="Use a launcher with a recent enough solver, or ask the administrator to install one.",
        evidence=[f"Solver versions of the launcher: {', '.join(facts.launcher_versions)}."],
    )


def infeasible_problem(facts: JobFacts) -> Cause | None:
    lines = facts.matching(
        r"\[(error|fatal)\].*(infeasib|unfeasib|no solution|unbounded|optimi[sz]ation failed|failed at week)"
    )
    if not lines:
        return None
    return Cause(
        code="infeasible_problem",
        confidence="high",
        title="The optimisation problem has no solution",
        explanation=(
            "For at least one week, the constraints of the study cannot all be satisfied together. Usual "
            "suspects: binding constraints, minimum stable power or must-run of thermal clusters, hydro "
            "reservoir levels and minimum generation, storage constraints, link capacities."
        ),
        suggestion=(
            "Find the year and week in the lines below, then check the constraints active at that time. "
            "`check_study` detects several classical inconsistencies. To investigate further, set the "
            "optimisation preference 'unfeasible problem behaviour' to export the MPS of the failing problem."
        ),
        evidence=lines,
    )


def out_of_memory(facts: JobFacts) -> Cause | None:
    lines = facts.matching(r"bad_alloc|out of memory|cannot allocate|not enough memory|oom[- ]kill|memory allocation")
    if not lines:
        return None
    return Cause(
        code="out_of_memory",
        confidence="high",
        title="The solver ran out of memory",
        explanation="The simulation needs more memory than the machine or the job was allowed to use.",
        suggestion=(
            "Reduce the number of years simulated in parallel (number of cores of the launch), or the size of "
            "the simulation (Monte-Carlo years, year-by-year outputs, output variables kept)."
        ),
        evidence=lines,
    )


def time_limit(facts: JobFacts) -> Cause | None:
    lines = facts.matching(r"time limit|timed? ?out|walltime|cancelled at .* due to")
    if not lines:
        return None
    return Cause(
        code="time_limit",
        confidence="high",
        title="The job reached its time limit",
        explanation="The launcher stopped the simulation because it ran longer than the time limit of the job.",
        suggestion="Launch again with a higher time limit, or with more cores.",
        evidence=lines,
    )


def missing_file(facts: JobFacts) -> Cause | None:
    lines = facts.matching(r"no such file|cannot open|could not open|failed to open|impossible to (open|read|load)")
    if not lines:
        return None
    return Cause(
        code="missing_input_file",
        confidence="medium",
        title="An input file is missing or unreadable",
        explanation="The solver could not open a file of the study it needs.",
        suggestion=(
            "The lines below name the file: check that the object it belongs to (area, cluster, link, "
            "constraint) is complete in the study."
        ),
        evidence=lines,
    )


def server_storage(facts: JobFacts) -> Cause | None:
    lines = facts.matching(r"permission denied|access denied|read-only file system|no space left")
    if not lines:
        return None
    return Cause(
        code="server_storage",
        confidence="high",
        title="The solver could not write on the server",
        explanation="A file permission or disk space problem on the server stopped the simulation.",
        suggestion="Report it to the administrator of Antares Web: the study data is not the cause.",
        evidence=lines,
    )


INVALID_DATA_WORDS = re.compile(
    r"invalid|incoherent|inconsisten|must be|out of bounds|wrong|mismatch|negative|not allowed", re.IGNORECASE
)


def invalid_data(facts: JobFacts) -> Cause | None:
    lines = [line for line in facts.solver_lines if is_error_line(line) and INVALID_DATA_WORDS.search(line)][
        -MAX_EVIDENCE_LINES:
    ]
    if not lines:
        return None
    return Cause(
        code="invalid_input_data",
        confidence="medium",
        title="The solver rejected some input data",
        explanation="The solver found values it does not accept in the input data of the study.",
        suggestion=(
            "The lines below name the area or the object concerned: fix the value in the study. "
            "`check_study` can find related inconsistencies."
        ),
        evidence=lines,
    )


RULES: list[Callable[[JobFacts], Cause | None]] = [
    no_solver_output,
    unreadable_study,
    no_compatible_solver,
    infeasible_problem,
    out_of_memory,
    time_limit,
    server_storage,
    missing_file,
    invalid_data,
]


def diagnose(facts: JobFacts, study_name: str | None = None) -> JobDiagnosis:
    causes = [cause for rule in RULES if (cause := rule(facts)) is not None]
    causes.sort(key=lambda cause: CONFIDENCE_ORDER[cause.confidence])  # stable: keeps the order of the rules
    error_lines = [line for line in facts.solver_lines if is_error_line(line)]
    notes = []
    if facts.job.status != "failed":
        notes.append(f"The job is '{facts.job.status}', not failed: the causes below may not apply.")
    elif not causes:
        notes.append(
            "No known failure pattern was recognised: read `error_lines` and `last_lines`, and use "
            "`get_job_logs` for more lines."
        )
    return JobDiagnosis(
        job=facts.job,
        study_name=study_name,
        study_version=facts.study_version,
        duration_seconds=facts.duration_seconds,
        launcher_solver_versions=facts.launcher_versions,
        causes=causes,
        error_lines=error_lines[-MAX_ERROR_LINES:],
        last_lines=[line for line in facts.stdout if not PREPARATION_LINES.match(line.strip())][-MAX_LAST_LINES:],
        notes=notes,
    )


async def _optional(awaitable: Awaitable[Any]) -> Any:
    """The study of an old job may have been deleted, and logs may be gone: diagnose with what is left."""
    try:
        return await awaitable
    except AntaresWebError:
        return None


def register(mcp: MCPServer, client: AntaresWebClient) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def diagnose_job(job_id: JobId) -> JobDiagnosis:
        """
        Find the probable causes of the failure of a simulation job: reads the job, its logs, the study
        version and the solver versions of its launcher, and matches them against known failure patterns
        (solver never started, solver version too old, infeasible problem, out of memory, time limit,
        missing file, invalid data...). Start here to explain a failed simulation; each cause comes with
        its evidence and a suggestion. Use `get_job_logs` to read more of the logs.
        """
        job = JobInfo.from_api(await guard(client.get_job(job_id)))
        stdout = await _optional(client.get_job_logs(job_id, log_type="STDOUT"))
        stderr = await _optional(client.get_job_logs(job_id, log_type="STDERR"))
        study = await _optional(client.get_study(job.study_id))
        launchers = await _optional(client.list_launchers()) or {}
        versions: list[Any] = next(
            (item.get("versions", []) for item in launchers.get("launchers", []) if item.get("id") == job.launcher),
            [],
        )
        facts = JobFacts(
            job=job,
            stdout=clean_lines(stdout or ""),
            stderr=clean_lines(stderr or ""),
            study_version=str(study["version"]) if study else None,
            launcher_versions=[str(version) for version in versions],
            duration_seconds=duration_between(job.created, job.completed),
        )
        diagnosis = diagnose(facts, study_name=study.get("name") if study else None)
        if study is None:
            diagnosis.notes.append("The study of this job cannot be read (deleted, or not accessible).")
        return diagnosis
