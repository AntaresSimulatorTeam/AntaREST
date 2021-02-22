import platform
from time import sleep, time
from uuid import uuid4

import pytest

from antarest.common.config import Config
from antarest.launcher.local_launcher import LocalLauncher
from antarest.launcher.model import JobResult, JobStatus


@pytest.mark.unit_test
def test_compute():
    local_launcher = LocalLauncher(Config())

    uuid = uuid4()

    expected_execution_result = JobResult(
        JobStatus.SUCCESS, msg="Hello, World!", exit_code=0
    )

    local_launcher._compute(
        antares_solver_path="echo", study_path="Hello, World!", uuid=uuid
    )

    assert expected_execution_result == local_launcher.results[uuid]


@pytest.mark.unit_test
def test_run_study():
    curl = "curl.exe" if platform.system() == "Windows" else "curl"
    config = Config({"launcher": {"type": "local", "binaries": {"42": curl}}})
    local_launcher = LocalLauncher(config)
    uuid = local_launcher.run_study(study_path="www.google.com", version="42")

    assert local_launcher.get_result(uuid) == JobResult(
        JobStatus.RUNNING, "", 0
    )

    t = time()
    result = local_launcher.get_result(uuid)
    while (result.job_status == JobStatus.RUNNING) and (time() - t) < 2:
        sleep(0.1)
        result = local_launcher.get_result(uuid)

    assert result.job_status == JobStatus.SUCCESS
    assert result.msg
