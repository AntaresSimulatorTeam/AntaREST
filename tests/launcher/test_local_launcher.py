# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.core.config import Config, LauncherConfig, LocalConfig
from antarest.launcher.adapters.abstractlauncher import LauncherInitException
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.model import JobStatus, LauncherParametersDTO

SOLVER_NAME = "solver.bat" if os.name == "nt" else "solver.sh"


@pytest.fixture
def launcher_config(tmp_path: Path) -> Config:
    """
    Fixture to create a launcher config with a local launcher.
    """
    solver_path = tmp_path.joinpath(SOLVER_NAME)
    data = {"binaries": {"700": solver_path}, "enable_nb_cores_detection": True}
    return Config(launcher=LauncherConfig(local=LocalConfig.from_dict(data)))


@pytest.mark.unit_test
def test_local_launcher__launcher_init_exception():
    with pytest.raises(
        LauncherInitException,
        match="Missing parameter 'launcher.local'",
    ):
        LocalLauncher(
            config=Config(launcher=LauncherConfig(local=None)),
            callbacks=Mock(),
            event_bus=Mock(),
            cache=Mock(),
        )


@pytest.mark.unit_test
def test_compute(tmp_path: Path, launcher_config: Config):
    local_launcher = LocalLauncher(launcher_config, callbacks=Mock(), event_bus=Mock(), cache=Mock())

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

    study_id = uuid.uuid4()
    local_launcher.job_id_to_study_id = {str(study_id): ("study-id", tmp_path / "run", Mock())}
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
    local_launcher._compute(
        antares_solver_path=solver_path,
        study_uuid="study-id",
        uuid=study_id,
        launcher_parameters=launcher_parameters,
    )

    # noinspection PyUnresolvedReferences
    local_launcher.callbacks.update_status.assert_has_calls(
        [
            call(str(study_id), JobStatus.RUNNING, None, None),
            call(str(study_id), JobStatus.SUCCESS, None, "some output"),
        ]
    )


@pytest.mark.unit_test
def test_select_best_binary(tmp_path: Path):
    binaries = {
        "700": Path("700"),
        "800": Path("800"),
        "900": Path("900"),
        "1000": Path("1000"),
    }
    local_launcher = LocalLauncher(
        Config(launcher=LauncherConfig(local=LocalConfig(binaries=binaries))),
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )

    assert local_launcher._select_best_binary("600") == binaries["700"]
    assert local_launcher._select_best_binary("700") == binaries["700"]
    assert local_launcher._select_best_binary("710") == binaries["800"]
    assert local_launcher._select_best_binary("1100") == binaries["1000"]
