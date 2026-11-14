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

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools.diagnosis import JobFacts, diagnose, duration_between, format_duration
from antares_web_mcp.tools.simulation import JobInfo
from tests.fake_antares_web import FakeAntaresWeb
from tests.helpers import STUDY_ID, call, data

JOB_ID = "faad6c7b-e93d-4a4c-9973-c578c5a4202b"
PREPARATION = ["Extracting study " + STUDY_ID, "Study extracted"]


def facts(
    *solver_lines: str,
    stderr: tuple[str, ...] = (),
    exit_code: int | None = 1,
    study_version: str = "8.8",
    launcher_versions: tuple[str, ...] = ("8.8", "10.2"),
    status: str = "failed",
    duration_seconds: int | None = 12,
) -> JobFacts:
    job = JobInfo(id=JOB_ID, study_id=STUDY_ID, status=status, exit_code=exit_code, launcher="local")
    return JobFacts(
        job=job,
        stdout=[*PREPARATION, *solver_lines],
        stderr=list(stderr),
        study_version=study_version,
        launcher_versions=list(launcher_versions),
        duration_seconds=duration_seconds,
    )


def codes(job_facts: JobFacts) -> list[str]:
    return [cause.code for cause in diagnose(job_facts).causes]


def test_solver_never_started() -> None:
    """Only the preparation lines of Antares Web, no exit code, a job of several days: a server-side failure."""
    diagnosis = diagnose(facts(exit_code=None, duration_seconds=3 * 86400 + 9 * 3600 + 35 * 60))

    (cause,) = diagnosis.causes
    assert (cause.code, cause.confidence) == ("solver_not_started", "high")
    assert "The job lasted 3 d 9 h 35 min." in cause.evidence
    assert "The study data is not the cause." in cause.explanation
    assert diagnosis.last_lines == []  # preparation lines are not solver output


def test_solver_crashed_without_output() -> None:
    assert codes(facts(exit_code=127)) == ["solver_crashed_at_start"]


def test_solver_version_too_old() -> None:
    error = "[solver][fatal] The folder `/tmp/job` does not seem to be a valid study"

    diagnosis = diagnose(facts("[solver][infos] Antares Solver v8.8.0", stderr=(error,), study_version="9.2"))

    (cause,) = diagnosis.causes
    assert cause.code == "solver_version_mismatch"
    assert "(9.2)" in cause.explanation and "8.8, 10.2" in cause.explanation
    assert cause.evidence == [error]
    assert diagnosis.error_lines == [error]


def test_no_solver_for_the_study_version() -> None:
    job_facts = facts("[solver][infos] starting", study_version="9.3", launcher_versions=("8.6", "880"))

    assert codes(job_facts) == ["no_compatible_solver"]
    assert codes(facts("[solver][infos] starting", study_version="9.3")) == []  # 10.2 can read a 9.3 study


@pytest.mark.parametrize(
    "line, expected",
    [
        ("[solver][error] Year 3, week 12: infeasible linear problem encountered", "infeasible_problem"),
        ("[2026-11-13 19:12:06][solver-0][fatal] Year 1 failed at week 1.", "infeasible_problem"),
        ("terminate called after throwing an instance of 'std::bad_alloc'", "out_of_memory"),
        ("slurmstepd: error: *** JOB 42 CANCELLED AT 2026-11-13 DUE TO TIME LIMIT ***", "time_limit"),
        ("[solver][error] I/O error: cannot open the file input/load/series/load_fr.txt", "missing_input_file"),
        ("[solver][fatal] /scratch/output: No space left on device", "server_storage"),
        ("[solver][error] fr: Invalid reservoir capacity.", "invalid_input_data"),
    ],
)
def test_known_failure_patterns(line: str, expected: str) -> None:
    diagnosis = diagnose(facts("[solver][infos] Loading the study", line))

    assert diagnosis.causes[0].code == expected
    assert diagnosis.causes[0].evidence == [line]


def test_causes_are_sorted_by_confidence() -> None:
    job_facts = facts(
        "[solver][error] fr: Invalid reservoir capacity.",
        "[solver][error] infeasible problem",
    )

    assert codes(job_facts) == ["infeasible_problem", "invalid_input_data"]


def test_unknown_failure_and_job_not_failed() -> None:
    unknown = diagnose(facts("[solver][infos] MC year 1", "[solver][fatal] Something unexpected"))
    running = diagnose(facts("[solver][infos] MC year 1", status="running", exit_code=None))

    assert unknown.causes == []
    assert unknown.error_lines == ["[solver][fatal] Something unexpected"]
    assert "No known failure pattern" in unknown.notes[0]
    assert "The job is 'running', not failed" in running.notes[0]


def test_error_lines_ignore_the_licence_banner_and_the_settings() -> None:
    diagnosis = diagnose(
        facts(
            "There are special exceptions to the terms and conditions of the licence",
            "[solver][infos] unfeasible problem behavior: error-verbose",
            "[solver-0][error] Linear optimization failed",
        )
    )

    assert diagnosis.error_lines == ["[solver-0][error] Linear optimization failed"]
    assert diagnosis.causes[0].evidence == ["[solver-0][error] Linear optimization failed"]


def test_durations() -> None:
    assert duration_between("2026-11-09 10:15:10.740752", "2026-11-12 19:50:29.891537") == 293719
    assert duration_between("2026-11-09 10:15:10", None) is None
    assert format_duration(293719) == "3 d 9 h 35 min 19 s"
    assert format_duration(0) == "0 s"


@pytest.mark.anyio
async def test_diagnose_job_tool(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    job: dict[str, Any] = {
        "id": JOB_ID,
        "study_id": STUDY_ID,
        "status": "failed",
        "launcher": "local_id",
        "exit_code": 1,
        "creation_date": "2026-11-13 10:00:00",
        "completion_date": "2026-11-13 10:00:05",
    }
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job)
    fake_api.route(
        "GET",
        f"/v1/launcher/jobs/{JOB_ID}/logs",
        params={"log_type": "STDOUT"},
        json_body="Extracting study\nStudy extracted\n[solver][infos] Antares Solver v8.8.0",
    )
    fake_api.route(
        "GET",
        f"/v1/launcher/jobs/{JOB_ID}/logs",
        params={"log_type": "STDERR"},
        json_body="[solver]\x1b[0;31m[fatal]\x1b[0m The folder `/tmp/x` does not seem to be a valid study",
    )
    fake_api.route("GET", f"/v1/studies/{STUDY_ID}", json_body={"id": STUDY_ID, "name": "Base", "version": "9.2"})
    fake_api.route(
        "GET",
        "/v1/launcher/launchers",
        json_body={"launchers": [{"id": "local_id", "versions": ["8.8", "10.2"]}, {"id": "other", "versions": []}]},
    )

    diagnosis = data(await call(api_client, "diagnose_job", {"job_id": JOB_ID}))

    assert diagnosis["study_name"] == "Base"
    assert diagnosis["duration_seconds"] == 5
    assert diagnosis["launcher_solver_versions"] == ["8.8", "10.2"]
    assert [cause["code"] for cause in diagnosis["causes"]] == ["solver_version_mismatch"]
    # Colour codes of the solver are removed
    assert diagnosis["error_lines"] == ["[solver][fatal] The folder `/tmp/x` does not seem to be a valid study"]


@pytest.mark.anyio
async def test_diagnose_job_of_a_deleted_study(fake_api: FakeAntaresWeb, api_client: AntaresWebClient) -> None:
    job = {"id": JOB_ID, "study_id": STUDY_ID, "status": "failed", "launcher": "local_id"}
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}", json_body=job)
    fake_api.route("GET", f"/v1/launcher/jobs/{JOB_ID}/logs", json_body="Extracting study\nStudy extracted")

    diagnosis = data(await call(api_client, "diagnose_job", {"job_id": JOB_ID}))

    assert diagnosis["study_version"] is None
    assert [cause["code"] for cause in diagnosis["causes"]] == ["solver_not_started"]
    assert "cannot be read" in diagnosis["notes"][-1]
