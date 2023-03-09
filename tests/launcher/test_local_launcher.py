from pathlib import Path
from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from antarest.core.config import Config, LauncherConfig, LocalConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.adapters.abstractlauncher import LauncherInitException
from antarest.launcher.adapters.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.model import JobStatus
from sqlalchemy import create_engine


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
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    storage_service = Mock()
    local_launcher = LocalLauncher(
        Config(), callbacks=Mock(), event_bus=Mock(), cache=Mock()
    )

    uuid = uuid4()
    local_launcher.job_id_to_study_id = {
        str(uuid): ("study-id", tmp_path / "run", Mock())
    }
    local_launcher.callbacks.import_output.return_value = "some output"
    local_launcher._compute(
        antares_solver_path="echo",
        study_uuid="study-id",
        uuid=uuid,
        launcher_parameters=None,
    )

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
