import os
import textwrap
from pathlib import Path
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from antarest.core.config import Config, LauncherConfig, LocalConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.adapters.abstractlauncher import LauncherInitException
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.model import JobStatus, LauncherParametersDTO


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
def test_compute(tmp_path: Path):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    local_launcher = LocalLauncher(Config(), callbacks=Mock(), event_bus=Mock(), cache=Mock())

    # prepare a dummy executable to simulate Antares Solver
    if os.name == "nt":
        solver_name = "solver.bat"
        solver_path = tmp_path.joinpath(solver_name)
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
        solver_name = "solver.sh"
        solver_path = tmp_path.joinpath(solver_name)
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

    uuid = uuid4()
    local_launcher.job_id_to_study_id = {str(uuid): ("study-id", tmp_path / "run", Mock())}
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
        uuid=uuid,
        launcher_parameters=launcher_parameters,
    )

    # noinspection PyUnresolvedReferences
    local_launcher.callbacks.update_status.assert_has_calls(
        [
            call(str(uuid), JobStatus.RUNNING, None, None),
            call(str(uuid), JobStatus.SUCCESS, None, "some output"),
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
