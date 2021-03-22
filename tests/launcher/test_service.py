from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from antarest.common.interfaces.eventbus import Event, EventType
from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.login.model import User
from antarest.common.requests import RequestParameters
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.service import LauncherService


@pytest.mark.unit_test
@patch.object(Auth, "get_current_user")
def test_service_run_study(get_current_user_mock):
    get_current_user_mock.return_value = None
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

    event_bus = Mock()

    running = JobResult(
        id=str(uuid), study_id="study_uuid", job_status=JobStatus.RUNNING
    )
    repository = Mock()
    repository.save.return_value = running

    launcher_service = LauncherService(
        config=Config(),
        storage_service=storage_service_mock,
        repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=event_bus,
    )

    job_id = launcher_service.run_study(
        "study_uuid",
        RequestParameters(user=User(id=0, name="admin", role="ADMIN")),
    )

    assert job_id == uuid
    repository.save.assert_called_once_with(running)
    event_bus.push.assert_called_once_with(
        Event(
            EventType.STUDY_JOB_STARTED,
            {"jid": str(uuid), "sid": "study_uuid"},
        )
    )


@pytest.mark.unit_test
def test_service_get_result_from_launcher():
    launcher_mock = Mock()
    fake_execution_result = JobResult(
        id=str(uuid4()),
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = launcher_mock

    repository = Mock()
    repository.get.return_value = fake_execution_result

    launcher_service = LauncherService(
        config=Config(),
        storage_service=Mock(),
        repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    job_id = uuid4()
    assert (
        launcher_service.get_result(job_uuid=job_id) == fake_execution_result
    )


@pytest.mark.unit_test
def test_service_get_result_from_database():
    launcher_mock = Mock()
    fake_execution_result = JobResult(
        id=str(uuid4()),
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    launcher_mock.get_result.return_value = None
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = launcher_mock

    repository = Mock()
    repository.get.return_value = fake_execution_result

    launcher_service = LauncherService(
        config=Config(),
        storage_service=Mock(),
        repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    assert (
        launcher_service.get_result(job_uuid=uuid4()) == fake_execution_result
    )


@pytest.mark.unit_test
def test_service_get_jobs_from_database():
    launcher_mock = Mock()
    fake_execution_result = [
        JobResult(
            id=str(uuid4()),
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
        )
    ]
    launcher_mock.get_result.return_value = None
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = launcher_mock

    repository = Mock()
    repository.find_by_study.return_value = fake_execution_result
    repository.get_all.return_value = fake_execution_result

    launcher_service = LauncherService(
        config=Config(),
        storage_service=Mock(),
        repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    study_id = uuid4()
    assert launcher_service.get_jobs(str(study_id)) == fake_execution_result
    repository.find_by_study.assert_called_once_with(str(study_id))
    assert launcher_service.get_jobs() == fake_execution_result
    repository.get_all.assert_called_once()
