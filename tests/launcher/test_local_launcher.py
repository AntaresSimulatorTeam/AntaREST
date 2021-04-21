from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.common.config import Config
from antarest.launcher.business.local_launcher.local_launcher import (
    LocalLauncher,
)
from antarest.launcher.model import JobResult, JobStatus


@pytest.mark.unit_test
def test_compute():
    local_launcher = LocalLauncher(Config(), storage_service=Mock())

    uuid = uuid4()

    expected_execution_result = JobResult(
        id=str(uuid),
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )

    callback = Mock()
    local_launcher.add_callback(callback)

    local_launcher._compute(
        antares_solver_path="echo", study_path="Hello, World!", uuid=uuid
    )

    callback.assert_called_once_with(expected_execution_result)
