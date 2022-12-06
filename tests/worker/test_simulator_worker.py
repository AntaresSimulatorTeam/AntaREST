import os
import platform
import stat
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from antarest.core.config import Config, LauncherConfig, LocalConfig
from antarest.worker.simulator_worker import (
    SimulatorWorker,
    GENERATE_KIRSHOFF_CONSTRAINTS_TASK_NAME,
    GENERATE_TIMESERIES_TASK_NAME,
)
from antarest.worker.worker import WorkerTaskCommand
from tests.conftest import with_db_context


@with_db_context
@patch("antarest.worker.simulator_worker.logger")
def test_execute_task(logger_mock: Mock, tmp_path: Path):
    simulator_mock_path = (
        Path(__file__).parent.parent / "integration" / "launcher_mock.sh"
    )
    st = os.stat(simulator_mock_path)
    os.chmod(simulator_mock_path, st.st_mode | stat.S_IEXEC)
    worker = SimulatorWorker(
        Mock(),
        Mock(),
        Config(
            launcher=LauncherConfig(
                local=LocalConfig(
                    binaries={
                        "800": simulator_mock_path,
                    }
                )
            )
        ),
    )
    worker.study_factory = Mock()

    with pytest.raises(NotImplementedError):
        worker.execute_task(
            task_info=WorkerTaskCommand(
                task_id="task_id", task_type="unknown", task_args={}
            )
        )

    with pytest.raises(NotImplementedError):
        worker.execute_task(
            task_info=WorkerTaskCommand(
                task_id="task_id",
                task_type=GENERATE_KIRSHOFF_CONSTRAINTS_TASK_NAME,
                task_args={},
            )
        )
    study_path = tmp_path / "study"
    result = worker.execute_task(
        task_info=WorkerTaskCommand(
            task_id="task_id",
            task_type=GENERATE_TIMESERIES_TASK_NAME,
            task_args={
                "study_id": "some_id",
                "managed": False,
                "study_path": str(study_path),
                "study_version": "800",
            },
        )
    )
    if not platform.platform().startswith("Windows"):
        assert result.success
        assert result.return_value == f"-i {study_path} -g\nexit 0\n"
    else:
        assert not result.success
