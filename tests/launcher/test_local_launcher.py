# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import textwrap
import uuid
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from antarest.core.config import Config, InvalidConfigurationError, Launcher, LauncherConfig, LocalConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.model import JobStatus, LauncherParametersDTO

SOLVER_NAME = "solver.bat" if os.name == "nt" else "solver.sh"


@pytest.fixture
def launcher_config(tmp_path: Path) -> Config:
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
    return Config(launcher=LauncherConfig(configs=[LocalConfig.from_dict(data)]))


@pytest.mark.unit_test
def test_local_launcher__launcher_init_exception():
    with pytest.raises(
        InvalidConfigurationError,
        match="Configuration is not available for the 'local_id' launcher",
    ):
        LocalLauncher(
            config=Config(launcher=LauncherConfig(configs=None)),
            launcher_id="local_id",
            callbacks=Mock(),
            event_bus=Mock(),
            cache=Mock(),
        )


@pytest.mark.unit_test
def test_compute(tmp_path: Path, launcher_config: Config):
    local_launcher = LocalLauncher(launcher_config, launcher_id="id", callbacks=Mock(), event_bus=Mock(), cache=Mock())

    # prepare a dummy executable to simulate Antares Solver
    if os.name == "nt":
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

    study_id = str(uuid.uuid4())
    local_launcher.job_id_to_study_id = {study_id: ("study-id", tmp_path / "run", Mock())}
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
        launcher_id="id",
    )
    local_launcher._compute(
        antares_solver_path=solver_path,
        study_uuid="study-id",
        job_id=study_id,
        launcher_parameters=launcher_parameters,
        current_user=DEFAULT_ADMIN_USER,
    )

    # noinspection PyUnresolvedReferences
    local_launcher.callbacks.update_status.assert_has_calls(
        [
            call(study_id, JobStatus.RUNNING, None, None),
            call(study_id, JobStatus.SUCCESS, None, "some output"),
        ]
    )


@pytest.mark.unit_test
def test_parse_launcher_arguments(launcher_config: Config):
    local_launcher = LocalLauncher(launcher_config, launcher_id="id", callbacks=Mock(), event_bus=Mock(), cache=Mock())
    launcher_parameters = LauncherParametersDTO(launcher_id="id", nb_cpu=4)
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters)
    assert sim_args == ["--force-parallel=4"]

    launcher_parameters = LauncherParametersDTO(launcher_id="id", nb_cpu=8)
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters)
    assert sim_args == ["--force-parallel=8"]

    launcher_parameters.other_options = "coin"
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters)
    assert sim_args == ["--force-parallel=8", "--use-ortools", "--ortools-solver=coin"]

    launcher_parameters.other_options = "xpress"
    sim_args, blabla = local_launcher._parse_launcher_options(launcher_parameters)
    assert sim_args == ["--force-parallel=8", "--use-ortools", "--ortools-solver=xpress"]

    launcher_parameters.other_options = "xpress presolve"
    sim_args, _ = local_launcher._parse_launcher_options(launcher_parameters)
    assert sim_args == [
        "--force-parallel=8",
        "--use-ortools",
        "--ortools-solver=xpress",
        "--solver-parameters",
        "PRESOLVE 1",
    ]

    os.environ["XPRESS_DIR"] = "fake_path_for_test"
    launcher_parameters.other_options = "xpress presolve"
    _, env_variables = local_launcher._parse_launcher_options(launcher_parameters)
    assert env_variables["XPRESS_DIR"] == "fake_path_for_test"


@pytest.mark.unit_test
def test_parse_xpress_dir(tmp_path: Path):
    data = {"id": "id", "name": "name", "type": "local", "xpress_dir": "fake_path_for_test"}
    launcher_config = Config(launcher=LauncherConfig(configs=[LocalConfig.from_dict(data)]))
    local_launcher = LocalLauncher(launcher_config, launcher_id="id", callbacks=Mock(), event_bus=Mock(), cache=Mock())
    _, env_variables = local_launcher._parse_launcher_options(LauncherParametersDTO())
    assert env_variables["XPRESS_DIR"] == "fake_path_for_test"


@pytest.mark.unit_test
def test_select_best_binary():
    binaries = {
        "700": Path("700"),
        "800": Path("800"),
        "900": Path("900"),
        "1000": Path("1000"),
    }
    local_launcher = LocalLauncher(
        Config(
            launcher=LauncherConfig(configs=[LocalConfig(id="id", name="name", type=Launcher.LOCAL, binaries=binaries)])
        ),
        launcher_id="id",
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )

    assert local_launcher._select_best_binary("600", "id") == binaries["700"]
    assert local_launcher._select_best_binary("700", "id") == binaries["700"]
    assert local_launcher._select_best_binary("710", "id") == binaries["800"]
    assert local_launcher._select_best_binary("1100", "id") == binaries["1000"]
