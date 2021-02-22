from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.common.config import Config
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.service import LauncherService
from antarest.storage.service import StorageService


@pytest.mark.unit_test
def test_service_run_study():
    storage_service_mock = Mock()
    storage_service_mock.get_study_information.return_value = {
        "antares": {"version": "42"}
    }
    storage_service_mock.get_study_path.return_value = Path("path/to/study")

    uuid = uuid4()
    launcher_mock = Mock()
    launcher_mock.run_study.return_value = uuid
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = launcher_mock

    launcher_service = LauncherService(
        config=Config(),
        storage_service=storage_service_mock,
        factory_launcher=factory_launcher_mock,
    )

    launcher_service.launcher.run_study.return_value = uuid

    job_id = launcher_service.run_study("study_uuid")

    assert job_id == uuid


@pytest.mark.unit_test
def test_service_get_result():
    storage_service_mock = Mock()
    launcher_mock = Mock()
    fake_execution_result = JobResult(
        JobStatus.SUCCESS, msg="Hello, World!", exit_code=0
    )
    launcher_mock.get_result.return_value = fake_execution_result
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = launcher_mock

    launcher_service = LauncherService(
        config=Config(),
        storage_service=storage_service_mock,
        factory_launcher=factory_launcher_mock,
    )

    assert (
        launcher_service.get_result(job_uuid=uuid4()) == fake_execution_result
    )
