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
Diagnosis of a failed simulation (`diagnose_job`, `diagnose_logs`).

`diagnose_job` gathers what Antares Web knows about a job (status, exit code, duration, logs, study
version, solver versions of the launcher) and matches it against known failure patterns. Like
`check_study`, the rules are deterministic and unit tested: the same job always gives the same
probable causes, and the model then explains them and digs further if needed.

`diagnose_logs` applies the same rules to logs given by the user, without a job: a large study is
often simulated on another server (a computing cluster), and only its logs are available next to
the study imported in Antares Web.

The patterns are heuristics on the solver logs: a cause is *probable*, with a confidence level
and the evidence it relies on, never a certainty.
"""

import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient, AntaresWebError
from antares_web_mcp.tools.common import READ_ONLY, JobId, StudyId, guard, parse_version
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
# First lines of the solver: "Antares Solver v8.8.6 (f10fa2b)".
SOLVER_VERSION_LINE = re.compile(r"antares[ _-]solver v?(\d+(?:\.\d+){1,2})", re.IGNORECASE)
# Logs given by the user can be the whole output of a long simulation: only the end is kept.
MAX_LOG_LINES = 50_000


class Cause(BaseModel):
    code: str = Field(description="Stable identifier of the failure pattern.")
    confidence: Confidence
    title: str
    explanation: str = Field(description="What probably happened.")
    suggestion: str = Field(description="What the user can do.")
    evidence: list[str] = Field(description="Log lines or facts the cause relies on.")


class LogsDiagnosis(BaseModel):
    source: str = Field(description="Where the logs come from: name of the attached file, or 'text'.")
    study_name: str | None = None
    study_version: str | None = None
    solver_version: str | None = Field(
        default=None, description="Version of the solver which wrote the logs (given, or read in the logs)."
    )
    line_count: int = Field(description="Number of non-empty lines read in the logs.")
    causes: list[Cause] = Field(description="Probable causes of the failure, most likely first.")
    error_lines: list[str] = Field(description=f"Last log lines mentioning an error (at most {MAX_ERROR_LINES}).")
    last_lines: list[str] = Field(description=f"Last lines of the logs (at most {MAX_LAST_LINES}).")
    notes: list[str]


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
    """Everything the rules need, gathered once. `job` is `None` for logs given by the user."""

    job: JobInfo | None
    stdout: list[str]
    stderr: list[str]
    study_version: str | None
    launcher_versions: list[str]
    duration_seconds: int | None
    solver_version: str | None = None
    """Version of the solver which wrote the logs, when known (logs given by the user)."""

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
    if facts.solver_lines or facts.job is None:
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
    versions = ""
    if facts.solver_version:
        versions = f" The logs were written by the solver {facts.solver_version}."
    elif facts.launcher_versions:
        versions = f" The launcher can run: {', '.join(facts.launcher_versions)}."
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


def solver_older_than_study(facts: JobFacts) -> Cause | None:
    """Logs given by the user: the solver which wrote them is compared with the version of the study."""
    if not facts.study_version or not facts.solver_version:
        return None
    try:
        # Major and minor only: a study in version 8.8 runs with the solver 8.8.6
        study = parse_version(facts.study_version)[:2]
        solver = parse_version(facts.solver_version)[:2]
    except ValueError:
        return None
    if study <= solver:
        return None
    return Cause(
        code="solver_older_than_study",
        confidence="medium",
        title="The solver is older than the study",
        explanation=(
            f"The logs were written by the solver {facts.solver_version}, but the study is in version "
            f"{facts.study_version}: an older solver cannot read a newer study. The study may also have been "
            f"upgraded since that simulation."
        ),
        suggestion="Launch again with a solver version equal to or higher than the study version.",
        evidence=[f"Solver version: {facts.solver_version}. Study version: {facts.study_version}."],
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
    solver_older_than_study,
    infeasible_problem,
    out_of_memory,
    time_limit,
    server_storage,
    missing_file,
    invalid_data,
]


def find_causes(facts: JobFacts) -> list[Cause]:
    causes = [cause for rule in RULES if (cause := rule(facts)) is not None]
    causes.sort(key=lambda cause: CONFIDENCE_ORDER[cause.confidence])  # stable: keeps the order of the rules
    return causes


def diagnose(facts: JobFacts, study_name: str | None = None) -> JobDiagnosis:
    assert facts.job is not None, "diagnose a job"
    causes = find_causes(facts)
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


def logs_text(text: str) -> str:
    """Logs saved from the REST API of Antares Web are a JSON string: decoded to the text it holds."""
    if text.lstrip().startswith('"'):
        try:
            decoded = json.loads(text)
        except ValueError:
            return text
        if isinstance(decoded, str):
            return decoded
    return text


def solver_version_in(lines: list[str]) -> str | None:
    """The version of the solver, as printed in its first lines."""
    return next((match.group(1) for line in lines if (match := SOLVER_VERSION_LINE.search(line))), None)


def diagnose_log_lines(
    lines: list[str],
    *,
    source: str,
    study_name: str | None = None,
    study_version: str | None = None,
    solver_version: str | None = None,
) -> LogsDiagnosis:
    """Applies the rules of `diagnose_job` to logs without a job: the solver version replaces the launcher."""
    solver_version = solver_version or solver_version_in(lines)
    facts = JobFacts(
        job=None,
        stdout=lines[-MAX_LOG_LINES:],
        stderr=[],
        study_version=study_version,
        launcher_versions=[],
        duration_seconds=None,
        solver_version=solver_version,
    )
    causes = find_causes(facts)
    notes = []
    if not facts.solver_lines:
        notes.append("The logs contain no line written by the solver: check that it is the right file.")
    elif not causes:
        notes.append("No known failure pattern was recognised: read `error_lines` and `last_lines`.")
    if len(lines) > MAX_LOG_LINES:
        notes.append(f"The logs have {len(lines)} lines: only the last {MAX_LOG_LINES} were analysed.")
    if study_version is None:
        notes.append("No study given: the solver version could not be compared with the study version.")
    return LogsDiagnosis(
        source=source,
        study_name=study_name,
        study_version=study_version,
        solver_version=solver_version,
        line_count=len(lines),
        causes=causes,
        error_lines=[line for line in facts.solver_lines if is_error_line(line)][-MAX_ERROR_LINES:],
        last_lines=facts.solver_lines[-MAX_LAST_LINES:],
        notes=notes,
    )


async def _optional(awaitable: Awaitable[Any]) -> Any:
    """The study of an old job may have been deleted, and logs may be gone: diagnose with what is left."""
    try:
        return await awaitable
    except AntaresWebError:
        return None


def register(mcp: MCPServer, client: AntaresWebClient, *, attachments: dict[str, str] | None = None) -> None:
    """
    Args:
        attachments: Files given by the user with their request (name -> text), e.g. logs uploaded in
            the web interface: `diagnose_logs` and `read_attachment` read them by name.
    """
    files = attachments or {}

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

    @mcp.tool(annotations=READ_ONLY)
    async def diagnose_logs(
        study_id: StudyId | None = None,
        attachment: str | None = None,
        logs: str | None = None,
        solver_version: str | None = None,
    ) -> LogsDiagnosis:
        """
        Find the probable causes of a failed simulation from its logs, when there is no job in Antares Web
        (e.g. a large study simulated on another server): same rules as `diagnose_job`. Give the logs
        either by the name of a file attached by the user (`attachment`), or as text (`logs`, for short
        excerpts only). Give the study the logs belong to (`study_id`) to compare its version with the
        solver version (read in the logs when not given).
        """
        if attachment is not None:
            if attachment not in files:
                names = ", ".join(files) or "none"
                raise ToolError(f"No attached file named {attachment!r}. Attached files: {names}.")
            text, source = files[attachment], attachment
        elif logs is not None:
            text, source = logs, "text"
        else:
            raise ToolError("Give the logs: `attachment` (name of an attached file) or `logs` (text).")
        study = await guard(client.get_study(study_id)) if study_id else None
        return diagnose_log_lines(
            clean_lines(logs_text(text)),
            source=source,
            study_name=study.get("name") if study else None,
            study_version=str(study["version"]) if study else None,
            solver_version=solver_version,
        )

    if files:

        @mcp.tool(annotations=READ_ONLY)
        async def read_attachment(name: str, pattern: str | None = None, last: int = 200) -> list[str]:
            """
            Read the lines of a file attached by the user (e.g. simulation logs): the `last` lines, or
            the last `last` lines matching the regular expression `pattern` (case-insensitive).
            """
            if name not in files:
                raise ToolError(f"No attached file named {name!r}. Attached files: {', '.join(files)}.")
            lines = clean_lines(logs_text(files[name]))
            if pattern:
                regex = re.compile(pattern, re.IGNORECASE)
                lines = [line for line in lines if regex.search(line)]
            return lines[-max(1, min(last, 2000)) :]
