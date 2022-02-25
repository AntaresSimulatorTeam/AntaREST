from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from antarest.core.config import (
    Config,
    LauncherConfig,
    SlurmConfig,
    LocalConfig,
)
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo
from antarest.core.requests import RequestParameters
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.service import LauncherService
from antarest.login.auth import Auth
from antarest.study.model import StudyMetadataDTO, OwnerInfo, PublicMode, Study


@pytest.mark.unit_test
@patch.object(Auth, "get_current_user")
def test_service_run_study(get_current_user_mock):
    get_current_user_mock.return_value = None
    storage_service_mock = Mock()
    storage_service_mock.get_study_information.return_value = StudyMetadataDTO(
        id="id",
        name="name",
        created=1,
        updated=1,
        type="rawstudy",
        owner=OwnerInfo(id=0, name="author"),
        groups=[],
        public_mode=PublicMode.NONE,
        version=42,
        workspace="default",
        managed=True,
        archived=False,
    )
    storage_service_mock.get_study_path.return_value = Path("path/to/study")

    uuid = uuid4()
    launcher_mock = Mock()
    launcher_mock.run_study.return_value = uuid
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = {
        "local": launcher_mock
    }

    event_bus = Mock()

    pending = JobResult(
        id=str(uuid),
        study_id="study_uuid",
        job_status=JobStatus.PENDING,
        launcher="local",
    )
    repository = Mock()
    repository.save.return_value = pending

    launcher_service = LauncherService(
        config=Config(),
        study_service=storage_service_mock,
        job_result_repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=event_bus,
    )

    job_id = launcher_service.run_study(
        "study_uuid",
        "local",
        None,
        RequestParameters(
            user=JWTUser(
                id=0,
                impersonator=0,
                type="users",
            )
        ),
    )

    assert job_id == str(uuid)
    repository.save.assert_called_once_with(pending)
    event_bus.push.assert_called_once_with(
        Event(
            type=EventType.STUDY_JOB_STARTED,
            payload=pending.to_dto().dict(),
            permissions=PermissionInfo(owner=0),
        )
    )


@pytest.mark.unit_test
def test_service_get_result_from_launcher():
    launcher_mock = Mock()
    fake_execution_result = JobResult(
        id=str(uuid4()),
        study_id="sid",
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
        launcher="local",
    )
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = {
        "local": launcher_mock
    }

    repository = Mock()
    repository.get.return_value = fake_execution_result

    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(),
        study_service=study_service,
        job_result_repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    job_id = uuid4()
    assert (
        launcher_service.get_result(
            job_uuid=job_id, params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        == fake_execution_result
    )


@pytest.mark.unit_test
def test_service_get_result_from_database():
    launcher_mock = Mock()
    fake_execution_result = JobResult(
        id=str(uuid4()),
        study_id="sid",
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    launcher_mock.get_result.return_value = None
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = {
        "local": launcher_mock
    }

    repository = Mock()
    repository.get.return_value = fake_execution_result

    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(),
        study_service=study_service,
        job_result_repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    assert (
        launcher_service.get_result(
            job_uuid=uuid4(), params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        == fake_execution_result
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
    factory_launcher_mock.build_launcher.return_value = {
        "local": launcher_mock
    }

    repository = Mock()
    repository.find_by_study.return_value = fake_execution_result
    repository.get_all.return_value = fake_execution_result

    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(),
        study_service=study_service,
        job_result_repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
    )

    study_id = uuid4()
    assert (
        launcher_service.get_jobs(
            str(study_id), params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        == fake_execution_result
    )
    repository.find_by_study.assert_called_once_with(str(study_id))
    assert (
        launcher_service.get_jobs(
            None, params=RequestParameters(user=DEFAULT_ADMIN_USER)
        )
        == fake_execution_result
    )
    repository.get_all.assert_called_once()


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "config_local,config_slurm,expected_output",
    [
        (None, None, {}),
        (
            None,
            SlurmConfig(antares_versions_on_remote_server=["42", "43"]),
            {"slurm": ["42", "43"]},
        ),
        (
            LocalConfig(binaries={"24": Path(), "34": Path()}),
            None,
            {"local": ["24", "34"]},
        ),
        (
            LocalConfig(binaries={"24": Path(), "34": Path()}),
            SlurmConfig(antares_versions_on_remote_server=["42", "43"]),
            {"local": ["24", "34"], "slurm": ["42", "43"]},
        ),
    ],
)
def test_service_get_versions(config_local, config_slurm, expected_output):
    config = Config(
        launcher=LauncherConfig(local=config_local, slurm=config_slurm)
    )
    launcher_service = LauncherService(
        config=config,
        study_service=Mock(),
        job_result_repository=Mock(),
        factory_launcher=Mock(),
        event_bus=Mock(),
    )

    assert expected_output == launcher_service.get_versions(params=Mock())


@pytest.mark.unit_test
def test_service_kill_job():
    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Mock(),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
    )
    launcher = "slurm"
    job_id = "job_id"
    job_result_mock = Mock()
    job_result_mock.id = job_id
    job_result_mock.study_id = "study_id"
    job_result_mock.launcher = launcher
    launcher_service.job_result_repository.get.return_value = job_result_mock
    launcher_service.launchers = {"slurm": Mock()}

    job_status = launcher_service.kill_job(
        job_id=job_id,
        params=RequestParameters(user=DEFAULT_ADMIN_USER),
    )

    launcher_service.launchers[launcher].kill_job.assert_called_once_with(
        job_id=job_id
    )

    assert job_status.job_status == JobStatus.FAILED
    launcher_service.job_result_repository.save.assert_called_once_with(
        job_status
    )
