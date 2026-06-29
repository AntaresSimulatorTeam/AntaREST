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

import os
import sys
import textwrap
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call

import pytest
from antares.study.version import SolverVersion

from antarest.core.config import LocalConfig
from antarest.core.exceptions import UnsupportedStudyVersion
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.model import JobStatus, LauncherParametersDTO, SolverPresets

SOLVER_NAME = "solver.bat" if sys.platform == "win32" else "solver.sh"


@pytest.fixture
def launcher_config(tmp_path: Path) -> LocalConfig:
    """
    Fixture to create a launcher config with a local launcher.
    """
    solver_path = tmp_path.joinpath(SOLVER_NAME)
    data = {
        "id": "id",
        "name": "name",
        "type": "local",
        "binaries": {"700": solver_path},
        "enable_nb_cores_detection": True,
        "local_workspace": tmp_path,
    }
    return LocalConfig.model_validate(data)


def test_compute(tmp_path: Path, launcher_config: LocalConfig) -> None:
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())

    # prepare a dummy executable to simulate Antares Solver
    if sys.platform == "win32":
        solver_path = tmp_path.joinpath(SOLVER_NAME)
        solver_path.write_text(
            textwrap.dedent(
                """\
                @echo off
                echo 'Dummy Solver is running...'
                exit 0
                """
            )
        )
    else:
        solver_path = tmp_path.joinpath(SOLVER_NAME)
        solver_path.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                echo 'Dummy Solver is running...'
                exit 0
                """
            )
        )
        solver_path.chmod(0o775)

    job_id = str(uuid.uuid4())
    local_launcher.job_id_to_study_id = {job_id: ("study-id", tmp_path / "run", Mock())}
    local_launcher.callbacks.import_output.return_value = "some output"
    launcher_parameters = LauncherParametersDTO(
        adequacy_patch=None,
        nb_cpu=8,
        post_processing=False,
        time_limit=3600,
        xpansion=False,
        xpansion_r_version=False,
        archive_output=False,
        auto_unzip=True,
        output_suffix="",
        other_options="",
    )
    local_launcher.submitted_jobs = {job_id: launcher_parameters}
    local_launcher._compute(
        antares_solver_path=solver_path,
        study_uuid="study-id",
        job_id=job_id,
        launcher_parameters=launcher_parameters,
        version=SolverVersion.parse("700"),
        current_user=DEFAULT_ADMIN_USER,
    )

    # noinspection PyUnresolvedReferences
    local_launcher.callbacks.update_status.assert_has_calls(
        [
            call(job_id, JobStatus.RUNNING, None, None),
            call(job_id, JobStatus.SUCCESS, None, "some output"),
        ]
    )


@pytest.fixture
def xpress_env() -> Any:
    """
    Defines XPRESSDIR env var and ensure removal after unit test
    """
    os.environ["XPRESSDIR"] = "fake_path_for_test"
    yield None
    del os.environ["XPRESSDIR"]


def test_parse_launcher_arguments(launcher_config: LocalConfig, xpress_env: Any) -> None:
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())
    solver_version_8_8 = SolverVersion.parse("8.8")
    solver_version_9_2 = SolverVersion.parse("9.2")
    solver_version_9_3 = SolverVersion.parse("9.3")

    # Easy cases
    launcher_parameters = LauncherParametersDTO(nb_cpu=4)
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, solver_version_8_8)
    assert sim_args == ["--force-parallel", "4"]

    launcher_parameters = LauncherParametersDTO(nb_cpu=8)
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, solver_version_8_8)
    assert sim_args == ["--force-parallel", "8"]

    launcher_parameters = LauncherParametersDTO(other_options="solver-logs")
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, solver_version_8_8)
    assert sim_args == ["--solver-logs"]

    launcher_parameters = LauncherParametersDTO(other_options="export-mps")
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, solver_version_8_8)
    assert sim_args == ["--named-mps-problems"]

    for solver in ["coin", "xpress"]:
        launcher_parameters = LauncherParametersDTO(other_options=solver)
        for version in [solver_version_8_8, solver_version_9_2, solver_version_9_3]:
            sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, version)
            if version == solver_version_8_8:
                assert sim_args == ["--use-ortools", "--ortools-solver", solver]
            elif version == solver_version_9_2 or version == solver_version_9_3:
                assert sim_args == ["--linear-solver", solver]

    # Xpress cases
    os.environ["XPRESSDIR"] = "fake_path_for_test"
    launcher_parameters.other_options = "xpress presolve"
    for version in [solver_version_9_2, solver_version_9_3]:
        sim_args, env_variables = local_launcher._parse_launcher_options(launcher_parameters, version)
        assert env_variables["XPRESSDIR"] == "fake_path_for_test"
        arg = "lp" if version == solver_version_9_2 else "linear"
        assert sim_args == [
            "--linear-solver",
            "xpress",
            f"--{arg}-solver-param-optim-1",
            "PRESOLVE 1",
            f"--{arg}-solver-param-optim-2",
            "PRESOLVE 1",
        ]

    launcher_parameters.other_options = 'xpress presolve param-optim1="THREADS 4"'
    for version in [solver_version_9_2, solver_version_9_3]:
        sim_args, env_variables = local_launcher._parse_launcher_options(launcher_parameters, version)
        assert env_variables["XPRESSDIR"] == "fake_path_for_test"
        arg = "lp" if version == solver_version_9_2 else "linear"
        assert sim_args == [
            "--linear-solver",
            "xpress",
            f"--{arg}-solver-param-optim-1",
            "PRESOLVE 1 THREADS 4",
            f"--{arg}-solver-param-optim-2",
            "PRESOLVE 1",
        ]

    options = 'xpress nobasis1 nobasis2 param-optim1="PRESOLVE 2 THREADS 4" param-optim2="LPFLAGS 5"'
    launcher_parameters = LauncherParametersDTO(other_options=options)
    for version in [solver_version_9_2, solver_version_9_3]:
        sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters, version)
        arg = "lp" if version == solver_version_9_2 else "linear"
        assert sim_args == [
            "--linear-solver",
            "xpress",
            "--use-optim-1-basis-next-week",
            "false",
            "--use-optim-1-basis-optim-2",
            "false",
            f"--{arg}-solver-param-optim-1",
            "PRESOLVE 2 THREADS 4",
            f"--{arg}-solver-param-optim-2",
            "LPFLAGS 5",
        ]


@pytest.mark.parametrize(
    "solver_version,arguments",
    [
        (SolverVersion.parse("8.7"), "xpress presolve"),
        (SolverVersion.parse("8.8"), "xpress nobasis1"),
        (SolverVersion.parse("8.8"), "xpress nobasis2"),
        (SolverVersion.parse("8.8"), 'xpress param-optim1="THREADS 4"'),
        (SolverVersion.parse("8.8"), 'xpress param-optim2="THREADS 4"'),
    ],
)
def test_unsupported_launcher_other_options_should_raise(
    launcher_config: LocalConfig, xpress_env: Any, solver_version: SolverVersion, arguments: str
) -> None:
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())
    launcher_parameters = LauncherParametersDTO(nb_cpu=4)
    with pytest.raises(ValueError, match="not supported"):
        launcher_parameters.other_options = arguments
        local_launcher._parse_launcher_options(launcher_parameters, solver_version)


def test_parse_xpress_dir(tmp_path: Path) -> None:
    data = {"id": "id", "name": "name", "type": "local", "xpress_dir": "fake_path_for_test"}
    launcher_config = LocalConfig.model_validate(data)
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())
    launch_parameters = LauncherParametersDTO(other_options="xpress")
    _, env_variables = local_launcher._parse_launcher_options(launch_parameters, SolverVersion.parse("9.2"))
    assert env_variables["XPRESSDIR"] == "fake_path_for_test"


def test_parse_solver_presets(launcher_config: LocalConfig):
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())
    launch_parameters = LauncherParametersDTO()
    solver_presets = SolverPresets.model_validate(
        {
            "id": "id-test-xpress-config",
            "name": "test-xpress-config",
            "linear_solver": "xpress",
            "min_antares_version": "9.2",
            "linear_solver_param_optim_1": {"THREADS": "4", "PRESOLVE": "1"},
            "linear_solver_param_optim_2": {"MIPRELSTOP": "0.01"},
            "linear_solver_param": {"DEFAULTALG": "4"},
            "use_optim_1_basis_next_week": True,
            "use_optim_1_basis_optim_2": False,
        }
    )
    launch_parameters.other_options = solver_presets.to_cli_options()
    args, _ = local_launcher._parse_launcher_options(launch_parameters, SolverVersion.parse("9.2"))
    assert args == [
        "--linear-solver",
        "xpress",
        "--use-optim-1-basis-optim-2",
        "false",
        "--lp-solver-param-optim-1",
        "DEFAULTALG 4 THREADS 4 PRESOLVE 1",
        "--lp-solver-param-optim-2",
        "DEFAULTALG 4 MIPRELSTOP 0.01",
    ]


def test_select_best_binary() -> None:
    binaries = {
        SolverVersion.parse("700"): Path("700"),
        SolverVersion.parse("800"): Path("800"),
        SolverVersion.parse("900"): Path("900"),
        SolverVersion.parse("1000"): Path("1000"),
    }
    local_launcher = LocalLauncher(
        LocalConfig.model_validate({"id": "id", "name": "name", "type": "local", "binaries": binaries}),
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )

    # Nominal cases
    assert local_launcher._select_best_binary(SolverVersion.parse("700")) == Path("700")
    assert local_launcher._select_best_binary(SolverVersion.parse("800")) == Path("800")
    assert local_launcher._select_best_binary(SolverVersion.parse("900")) == Path("900")
    assert local_launcher._select_best_binary(SolverVersion.parse("1000")) == Path("1000")

    # Missing solvers
    with pytest.raises(UnsupportedStudyVersion, match="Solver version 6 not found in the application config"):
        local_launcher._select_best_binary(SolverVersion.parse("600"))
