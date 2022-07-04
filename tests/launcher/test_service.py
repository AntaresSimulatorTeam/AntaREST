import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, call
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from antarest.core.config import (
    Config,
    LauncherConfig,
    SlurmConfig,
    LocalConfig,
    StorageConfig,
)
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.filetransfer.model import (
    FileDownloadTaskDTO,
    FileDownloadDTO,
    FileDownload,
)
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
from antarest.launcher.model import (
    JobResult,
    JobStatus,
    LogType,
    JobLog,
    JobLogType,
)
from antarest.launcher.service import (
    LauncherService,
    ORPHAN_JOBS_VISIBILITY_THRESHOLD,
    JobNotFound,
    LAUNCHER_PARAM_NAME_SUFFIX,
)
from antarest.login.auth import Auth
from antarest.login.model import User
from antarest.study.model import StudyMetadataDTO, OwnerInfo, PublicMode, Study
from tests.conftest import with_db_context


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
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )
    launcher_service._generate_new_id = lambda: str(uuid)

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
        file_transfer_manager=Mock(),
        task_service=Mock(),
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
        file_transfer_manager=Mock(),
        task_service=Mock(),
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
    now = datetime.utcnow()
    fake_execution_result = [
        JobResult(
            id=str(uuid4()),
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
        )
    ]
    returned_faked_execution_results = [
        JobResult(
            id="1",
            study_id="a",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
            creation_date=now,
        ),
        JobResult(
            id="2",
            study_id="b",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
            creation_date=now,
        ),
    ]
    all_faked_execution_results = returned_faked_execution_results + [
        JobResult(
            id="3",
            study_id="c",
            job_status=JobStatus.SUCCESS,
            msg="Hello, World!",
            exit_code=0,
            creation_date=now
            - timedelta(days=ORPHAN_JOBS_VISIBILITY_THRESHOLD + 1),
        )
    ]
    launcher_mock.get_result.return_value = None
    factory_launcher_mock = Mock()
    factory_launcher_mock.build_launcher.return_value = {
        "local": launcher_mock
    }

    repository = Mock()
    repository.find_by_study.return_value = fake_execution_result
    repository.get_all.return_value = all_faked_execution_results

    study_service = Mock()
    study_service.get_study.side_effect = [
        Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE),
        Mock(spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE),
        StudyNotFoundError(""),
        StudyNotFoundError(""),
        Mock(
            spec=Study,
            groups=[],
            owner=User(id=2),
            public_mode=PublicMode.NONE,
        ),
        StudyNotFoundError(""),
        StudyNotFoundError(""),
    ]

    launcher_service = LauncherService(
        config=Config(),
        study_service=study_service,
        job_result_repository=repository,
        factory_launcher=factory_launcher_mock,
        event_bus=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
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
        == all_faked_execution_results
    )
    assert (
        launcher_service.get_jobs(
            None,
            params=RequestParameters(
                user=JWTUser(
                    id=2,
                    impersonator=2,
                    type="users",
                    groups=[],
                )
            ),
        )
        == returned_faked_execution_results
    )

    with pytest.raises(UserHasNotPermissionError):
        launcher_service.remove_job(
            "some job",
            RequestParameters(
                user=JWTUser(
                    id=2,
                    impersonator=2,
                    type="users",
                    groups=[],
                )
            ),
        )

    launcher_service.remove_job(
        "some job", RequestParameters(user=DEFAULT_ADMIN_USER)
    )
    repository.delete.assert_called_with("some job")


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
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )

    assert expected_output == launcher_service.get_versions(params=Mock())


@pytest.mark.unit_test
def test_service_kill_job(tmp_path: Path):
    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
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


def test_append_logs(tmp_path: Path):
    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )
    launcher = "slurm"
    job_id = "job_id"
    job_result_mock = Mock()
    job_result_mock.id = job_id
    job_result_mock.study_id = "study_id"
    job_result_mock.output_id = None
    job_result_mock.launcher = launcher
    job_result_mock.logs = []
    launcher_service.job_result_repository.get.return_value = job_result_mock

    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    launcher_service.append_log(job_id, "test", JobLogType.BEFORE)
    launcher_service.job_result_repository.save.assert_called_with(
        job_result_mock
    )
    assert job_result_mock.logs[0].message == "test"
    assert job_result_mock.logs[0].job_id == "job_id"
    assert job_result_mock.logs[0].log_type == str(JobLogType.BEFORE)


def test_get_logs(tmp_path: Path):
    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )
    launcher = "slurm"
    job_id = "job_id"
    job_result_mock = Mock()
    job_result_mock.id = job_id
    job_result_mock.study_id = "study_id"
    job_result_mock.output_id = None
    job_result_mock.launcher = launcher
    job_result_mock.logs = [
        JobLog(message="first message", log_type=str(JobLogType.BEFORE)),
        JobLog(message="second message", log_type=str(JobLogType.BEFORE)),
        JobLog(message="last message", log_type=str(JobLogType.AFTER)),
    ]
    job_result_mock.launcher_params = '{"archive_output": false}'

    launcher_service.job_result_repository.get.return_value = job_result_mock
    slurm_launcher = Mock()
    launcher_service.launchers = {"slurm": slurm_launcher}
    slurm_launcher.get_log.return_value = "launcher logs"

    logs = launcher_service.get_log(
        job_id, LogType.STDOUT, RequestParameters(DEFAULT_ADMIN_USER)
    )
    assert logs == "first message\nsecond message\nlauncher logs\nlast message"
    logs = launcher_service.get_log(
        job_id, LogType.STDERR, RequestParameters(DEFAULT_ADMIN_USER)
    )
    assert logs == "launcher logs"

    study_service.get.side_effect = [b"", b"some sim log", b"error log"]
    job_result_mock.output_id = "some id"
    logs = launcher_service.get_log(
        job_id, LogType.STDOUT, RequestParameters(DEFAULT_ADMIN_USER)
    )
    assert logs == "first message\nsecond message\nsome sim log\nlast message"

    logs = launcher_service.get_log(
        job_id, LogType.STDERR, RequestParameters(DEFAULT_ADMIN_USER)
    )
    assert logs == "error log"

    study_service.get.assert_has_calls(
        [
            call(
                "study_id",
                f"/output/some id/antares-out",
                depth=1,
                formatted=True,
                params=RequestParameters(DEFAULT_ADMIN_USER),
            ),
            call(
                "study_id",
                f"/output/some id/simulation",
                depth=1,
                formatted=True,
                params=RequestParameters(DEFAULT_ADMIN_USER),
            ),
            call(
                "study_id",
                f"/output/some id/antares-err",
                depth=1,
                formatted=True,
                params=RequestParameters(DEFAULT_ADMIN_USER),
            ),
        ]
    )


def test_manage_output(tmp_path: Path):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Mock(storage=StorageConfig(tmp_dir=tmp_path)),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )

    output_path = tmp_path / "new_output"
    os.mkdir(output_path)
    (output_path / "log").touch()
    (output_path / "data").touch()
    additional_log = tmp_path / "output.log"
    additional_log.write_text("some log")
    job_id = "job_id"
    study_id = "study_id"
    launcher_service.job_result_repository.get.side_effect = [
        None,
        JobResult(id=job_id, study_id=study_id),
        JobResult(id=job_id, study_id=study_id, output_id="some id"),
        JobResult(
            id=job_id,
            study_id=study_id,
        ),
        JobResult(
            id=job_id,
            study_id=study_id,
            launcher_params=json.dumps(
                {
                    "archive_output": False,
                    f"{LAUNCHER_PARAM_NAME_SUFFIX}": "hello",
                }
            ),
        ),
    ]
    with pytest.raises(JobNotFound):
        launcher_service._import_output(
            job_id, output_path, {"out.log": [additional_log]}
        )

    launcher_service._import_output(
        job_id, output_path, {"out.log": [additional_log]}
    )
    assert not launcher_service._get_job_output_fallback_path(job_id).exists()
    launcher_service.study_service.import_output.assert_called()

    launcher_service.download_output(
        "job_id", RequestParameters(DEFAULT_ADMIN_USER)
    )
    launcher_service.study_service.export_output.assert_called()

    launcher_service.study_service.import_output.side_effect = [
        StudyNotFoundError(""),
        StudyNotFoundError(""),
    ]

    assert (
        launcher_service._import_output(
            job_id, output_path, {"out.log": [additional_log]}
        )
        is None
    )

    (output_path / "info.antares-output").write_text(
        f"[general]\nmode=eco\nname=foo\ntimestamp={time.time()}"
    )
    output_name = launcher_service._import_output(
        job_id, output_path, {"out.log": [additional_log]}
    )
    assert output_name is not None
    assert output_name.endswith("-hello")
    assert launcher_service._get_job_output_fallback_path(job_id).exists()
    assert (
        launcher_service._get_job_output_fallback_path(job_id)
        / output_name
        / "out.log"
    ).exists()

    launcher_service.job_result_repository.get.reset_mock()
    launcher_service.job_result_repository.get.side_effect = [
        None,
        JobResult(id=job_id, study_id=study_id, output_id=output_name),
    ]
    with pytest.raises(JobNotFound):
        launcher_service.download_output(
            "job_id", RequestParameters(DEFAULT_ADMIN_USER)
        )

    study_service.get_study.reset_mock()
    study_service.get_study.side_effect = StudyNotFoundError("")

    export_file = FileDownloadDTO(id="a", name="a", filename="a", ready=True)
    launcher_service.file_transfer_manager.request_download.return_value = (
        FileDownload(id="a", name="a", filename="a", ready=True, path="a")
    )
    launcher_service.task_service.add_task.return_value = "some id"

    assert launcher_service.download_output(
        "job_id", RequestParameters(DEFAULT_ADMIN_USER)
    ) == FileDownloadTaskDTO(task="some id", file=export_file)

    launcher_service.remove_job(
        job_id, RequestParameters(user=DEFAULT_ADMIN_USER)
    )
    assert not launcher_service._get_job_output_fallback_path(job_id).exists()


def test_save_stats(tmp_path: Path) -> None:
    study_service = Mock()
    study_service.get_study.return_value = Mock(
        spec=Study, groups=[], owner=None, public_mode=PublicMode.NONE
    )

    launcher_service = LauncherService(
        config=Mock(storage=StorageConfig(tmp_dir=tmp_path)),
        study_service=study_service,
        job_result_repository=Mock(),
        event_bus=Mock(),
        factory_launcher=Mock(),
        file_transfer_manager=Mock(),
        task_service=Mock(),
    )

    job_id = "job_id"
    study_id = "study_id"
    job_result = JobResult(
        id=job_id, study_id=study_id, job_status=JobStatus.SUCCESS
    )

    output_path = tmp_path / "some-output"
    output_path.mkdir()

    launcher_service._save_solver_stats(job_result, output_path)
    launcher_service.job_result_repository.save.assert_not_called()

    expected_saved_stats = """#item	duration_ms	NbOccurences
mc_years	216328	1
study_loading	4304	1
survey_report	158	1
total	244581	1
tsgen_hydro	1683	1
tsgen_load	2702	1
tsgen_solar	21606	1
tsgen_thermal	407	2
tsgen_wind	2500	1
    """
    (output_path / "time_measurement.txt").write_text(expected_saved_stats)

    launcher_service._save_solver_stats(job_result, output_path)
    launcher_service.job_result_repository.save.assert_called_with(
        JobResult(
            id=job_id,
            study_id=study_id,
            job_status=JobStatus.SUCCESS,
            solver_stats=expected_saved_stats,
        )
    )
