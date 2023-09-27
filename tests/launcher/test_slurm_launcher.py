import os
import shutil
import textwrap
import uuid
from argparse import Namespace
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters
from antareslauncher.study_dto import StudyDTO
from sqlalchemy import create_engine

from antarest.core.config import Config, LauncherConfig, SlurmConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.adapters.abstractlauncher import LauncherInitException
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import (
    LOG_DIR_NAME,
    MAX_TIME_LIMIT,
    MIN_TIME_LIMIT,
    WORKSPACE_LOCK_FILE_NAME,
    SlurmLauncher,
    VersionNotSupportedError,
)
from antarest.launcher.model import JobStatus, LauncherParametersDTO
from antarest.tools.admin_lib import clean_locks_from_config


@pytest.fixture
def launcher_config(tmp_path: Path) -> Config:
    return Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                local_workspace=tmp_path,
                default_json_db_name="default_json_db_name",
                slurm_script_path="slurm_script_path",
                antares_versions_on_remote_server=["42", "45"],
                username="username",
                hostname="hostname",
                port=42,
                private_key_file=Path("private_key_file"),
                key_password="key_password",
                password="password",
            )
        )
    )


@pytest.mark.unit_test
def test_slurm_launcher__launcher_init_exception():
    with pytest.raises(
        LauncherInitException,
        match="Missing parameter 'launcher.slurm'",
    ):
        SlurmLauncher(
            config=Config(launcher=LauncherConfig(slurm=None)),
            callbacks=Mock(),
            event_bus=Mock(),
            cache=Mock(),
        )


@pytest.mark.unit_test
def test_init_slurm_launcher_arguments(tmp_path: Path):
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                default_wait_time=42,
                default_time_limit=43,
                default_n_cpu=44,
                local_workspace=tmp_path,
            )
        )
    )

    slurm_launcher = SlurmLauncher(config=config, callbacks=Mock(), event_bus=Mock(), cache=Mock())

    arguments = slurm_launcher._init_launcher_arguments()

    assert not arguments.wait_mode
    assert not arguments.check_queue
    assert not arguments.wait_mode
    assert not arguments.check_queue
    assert arguments.json_ssh_config is None
    assert arguments.job_id_to_kill is None
    assert not arguments.xpansion_mode
    assert not arguments.version
    assert not arguments.post_processing
    assert Path(arguments.studies_in) == config.launcher.slurm.local_workspace / "STUDIES_IN"
    assert Path(arguments.output_dir) == config.launcher.slurm.local_workspace / "OUTPUT"
    assert Path(arguments.log_dir) == config.launcher.slurm.local_workspace / "LOGS"


@pytest.mark.unit_test
def test_init_slurm_launcher_parameters(tmp_path: Path):
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                local_workspace=tmp_path,
                default_json_db_name="default_json_db_name",
                slurm_script_path="slurm_script_path",
                antares_versions_on_remote_server=["42"],
                username="username",
                hostname="hostname",
                port=42,
                private_key_file=Path("private_key_file"),
                key_password="key_password",
                password="password",
            )
        )
    )

    slurm_launcher = SlurmLauncher(config=config, callbacks=Mock(), event_bus=Mock(), cache=Mock())

    main_parameters = slurm_launcher._init_launcher_parameters()
    assert main_parameters.json_dir == config.launcher.slurm.local_workspace
    assert main_parameters.default_json_db_name == config.launcher.slurm.default_json_db_name
    assert main_parameters.slurm_script_path == config.launcher.slurm.slurm_script_path
    assert main_parameters.antares_versions_on_remote_server == config.launcher.slurm.antares_versions_on_remote_server
    assert main_parameters.default_ssh_dict == {
        "username": config.launcher.slurm.username,
        "hostname": config.launcher.slurm.hostname,
        "port": config.launcher.slurm.port,
        "private_key_file": config.launcher.slurm.private_key_file,
        "key_password": config.launcher.slurm.key_password,
        "password": config.launcher.slurm.password,
    }
    assert main_parameters.db_primary_key == "name"


@pytest.mark.unit_test
def test_slurm_launcher_delete_function(tmp_path: str):
    config = Config(launcher=LauncherConfig(slurm=SlurmConfig(local_workspace=Path(tmp_path))))
    slurm_launcher = SlurmLauncher(
        config=config,
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
        cache=Mock(),
    )
    directory_path = Path(tmp_path) / "directory"
    directory_path.mkdir()
    (directory_path / "file.txt").touch()

    file_path = Path(tmp_path) / "some.log"
    file_path.touch()
    assert file_path.exists()

    slurm_launcher._delete_workspace_file(directory_path)
    slurm_launcher._delete_workspace_file(file_path)

    assert not directory_path.exists()
    assert not file_path.exists()


def test_extra_parameters(launcher_config: Config):
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )
    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO())
    assert launcher_params.n_cpu == 1
    assert launcher_params.time_limit == 0
    assert not launcher_params.xpansion_mode
    assert not launcher_params.post_processing

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(nb_cpu=12))
    assert launcher_params.n_cpu == 12

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(nb_cpu=48))
    assert launcher_params.n_cpu == 1

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(time_limit=10))
    assert launcher_params.time_limit == MIN_TIME_LIMIT

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(time_limit=999999999))
    assert launcher_params.time_limit == MAX_TIME_LIMIT - 3600

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(time_limit=99999))
    assert launcher_params.time_limit == 99999

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(xpansion=True))
    assert launcher_params.xpansion_mode

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(post_processing=True))
    assert launcher_params.post_processing

    launcher_params = slurm_launcher._check_and_apply_launcher_params(LauncherParametersDTO(adequacy_patch={}))
    assert launcher_params.post_processing


# noinspection PyUnresolvedReferences
@pytest.mark.parametrize(
    "version, job_status",
    [(42, JobStatus.RUNNING), (99, JobStatus.FAILED), (45, JobStatus.FAILED)],
)
@pytest.mark.unit_test
def test_run_study(
    tmp_path: Path,
    launcher_config: Config,
    version: int,
    job_status: JobStatus,
):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )

    study_uuid = "study_uuid"
    argument = Mock()
    argument.studies_in = launcher_config.launcher.slurm.local_workspace / "studies_in"
    slurm_launcher.launcher_args = argument
    slurm_launcher._clean_local_workspace = Mock()
    slurm_launcher.start = Mock()
    slurm_launcher._delete_workspace_file = Mock()

    job_id = str(uuid.uuid4())
    study_dir = argument.studies_in / job_id
    study_dir.mkdir(parents=True)
    (study_dir / "study.antares").write_text(
        textwrap.dedent(
            """\
            [antares]
            version=1
            """
        )
    )

    # noinspection PyUnusedLocal
    def call_launcher_mock(arguments: Namespace, parameters: MainParameters):
        if version != 45:
            slurm_launcher.data_repo_tinydb.save_study(StudyDTO(job_id))

    slurm_launcher._call_launcher = call_launcher_mock

    if version == 99:
        with pytest.raises(VersionNotSupportedError):
            slurm_launcher._run_study(study_uuid, job_id, LauncherParametersDTO(), str(version))
    else:
        slurm_launcher._run_study(study_uuid, job_id, LauncherParametersDTO(), str(version))

    assert (
        version not in launcher_config.launcher.slurm.antares_versions_on_remote_server
        or f"solver_version = {version}" in (study_dir / "study.antares").read_text(encoding="utf-8")
    )
    #    slurm_launcher._clean_local_workspace.assert_called_once()
    slurm_launcher.callbacks.export_study.assert_called_once()
    slurm_launcher.callbacks.update_status.assert_called_once_with(ANY, job_status, ANY, None)
    if job_status == JobStatus.RUNNING:
        slurm_launcher.start.assert_called_once()
        slurm_launcher._delete_workspace_file.assert_called_once()


@pytest.mark.unit_test
def test_check_state(tmp_path: Path, launcher_config: Config):
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        cache=Mock(),
    )
    slurm_launcher._import_study_output = Mock()
    slurm_launcher._delete_workspace_file = Mock()
    slurm_launcher.stop = Mock()

    study1 = Mock()
    study1.done = True
    study1.name = "job_id1"
    study1.with_error = False
    study1.job_log_dir = tmp_path / "job_id1"

    study2 = Mock()
    study2.done = True
    study2.name = "job_id2"
    study2.with_error = True
    study2.job_log_dir = tmp_path / "job_id2"

    data_repo_tinydb = Mock()
    data_repo_tinydb.get_list_of_studies = Mock(return_value=[study1, study2])
    data_repo_tinydb.remove_study = Mock()

    slurm_launcher.launcher_params = Mock()
    slurm_launcher.launcher_args = Mock()
    slurm_launcher.data_repo_tinydb = data_repo_tinydb

    slurm_launcher._check_studies_state()

    # noinspection PyUnresolvedReferences
    assert slurm_launcher.callbacks.update_status.call_count == 2
    assert slurm_launcher._import_study_output.call_count == 2
    assert slurm_launcher._delete_workspace_file.call_count == 4
    assert data_repo_tinydb.remove_study.call_count == 2
    slurm_launcher.stop.assert_called_once()


@pytest.mark.unit_test
def test_clean_local_workspace(tmp_path: Path, launcher_config: Config):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    # noinspection SpellCheckingInspection
    DBSessionMiddleware(
        None,
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
        cache=Mock(),
    )

    (launcher_config.launcher.slurm.local_workspace / "machin.txt").touch()

    assert os.listdir(launcher_config.launcher.slurm.local_workspace)
    slurm_launcher._clean_local_workspace()
    assert not os.listdir(launcher_config.launcher.slurm.local_workspace)


# noinspection PyUnresolvedReferences
@pytest.mark.unit_test
def test_import_study_output(launcher_config, tmp_path):
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
        cache=Mock(),
    )
    slurm_launcher.callbacks.import_output.return_value = "output"
    res = slurm_launcher._import_study_output("1")

    slurm_launcher.callbacks.import_output.assert_called_once_with(
        "1",
        launcher_config.launcher.slurm.local_workspace / "OUTPUT" / "1" / "output",
        {},
    )
    assert res == "output"

    link_dir = launcher_config.launcher.slurm.local_workspace / "OUTPUT" / "1" / "input" / "links"
    link_dir.mkdir(parents=True)
    link_file = link_dir / "something"
    link_file.write_text("hello")
    xpansion_dir = Path(launcher_config.launcher.slurm.local_workspace / "OUTPUT" / "1" / "user" / "expansion")
    xpansion_dir.mkdir(parents=True)
    xpansion_test_file = xpansion_dir / "something_else"
    xpansion_test_file.write_text("world")
    output_dir = launcher_config.launcher.slurm.local_workspace / "OUTPUT" / "1" / "output" / "output_name"
    output_dir.mkdir(parents=True)
    assert not (output_dir / "updated_links" / "something").exists()
    assert not (output_dir / "updated_links" / "something").exists()

    slurm_launcher._import_study_output("1", "cpp")
    assert (output_dir / "updated_links" / "something").exists()
    assert (output_dir / "updated_links" / "something").read_text() == "hello"
    shutil.rmtree(output_dir / "updated_links")

    slurm_launcher._import_study_output("1", "r")
    assert (output_dir / "results" / "something_else").exists()
    assert (output_dir / "results" / "something_else").read_text() == "world"

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_info = log_dir / "antares-out-xxxx.txt"
    log_error = log_dir / "antares-err-xxxx.txt"
    log_info.touch()
    log_error.touch()
    slurm_launcher.callbacks.import_output.reset_mock()
    slurm_launcher._import_study_output("1", None, str(log_dir))
    slurm_launcher.callbacks.import_output.assert_called_once_with(
        "1",
        launcher_config.launcher.slurm.local_workspace / "OUTPUT" / "1" / "output",
        {
            "antares-out.log": [log_info],
            "antares-err.log": [log_error],
        },
    )


@patch("antarest.launcher.adapters.slurm_launcher.slurm_launcher.run_with")
@pytest.mark.unit_test
def test_kill_job(
    run_with_mock,
    tmp_path: Path,
    launcher_config: Config,
):
    launch_id = "launch_id"
    mock_study = Mock()
    mock_study.name = launch_id
    mock_study.job_id = 42

    data_repo_tinydb_mock = Mock(spec=DataRepoTinydb)
    data_repo_tinydb_mock.get_list_of_studies.return_value = [mock_study]

    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
        cache=Mock(),
    )
    slurm_launcher.data_repo_tinydb = data_repo_tinydb_mock

    slurm_launcher.kill_job(job_id=launch_id)

    launcher_arguments = Namespace(
        antares_version=0,
        check_queue=False,
        job_id_to_kill=42,
        json_ssh_config=None,
        log_dir=str(tmp_path / "LOGS"),
        n_cpu=1,
        output_dir=str(tmp_path / "OUTPUT"),
        post_processing=False,
        studies_in=str(tmp_path / "STUDIES_IN"),
        time_limit=0,
        version=False,
        wait_mode=False,
        wait_time=0,
        xpansion_mode=None,
        other_options=None,
    )
    launcher_parameters = MainParameters(
        json_dir=Path(tmp_path),
        default_json_db_name="default_json_db_name",
        slurm_script_path="slurm_script_path",
        antares_versions_on_remote_server=["42", "45"],
        default_ssh_dict={
            "username": "username",
            "hostname": "hostname",
            "port": 42,
            "private_key_file": Path("private_key_file"),
            "key_password": "key_password",
            "password": "password",
        },
        db_primary_key="name",
    )

    run_with_mock.assert_called_with(launcher_arguments, launcher_parameters, show_banner=False)


@patch("antarest.launcher.adapters.slurm_launcher.slurm_launcher.run_with")
def test_launcher_workspace_init(run_with_mock, tmp_path: Path, launcher_config: Config):
    callbacks = Mock()
    (tmp_path / LOG_DIR_NAME).mkdir()

    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        callbacks=callbacks,
        event_bus=Mock(),
        retrieve_existing_jobs=True,
        cache=Mock(),
    )
    workspaces = [p for p in tmp_path.iterdir() if p.is_dir() and p.name != LOG_DIR_NAME]
    assert len(workspaces) == 1
    assert (workspaces[0] / WORKSPACE_LOCK_FILE_NAME).exists()

    clean_locks_from_config(launcher_config)
    assert not (workspaces[0] / WORKSPACE_LOCK_FILE_NAME).exists()

    slurm_launcher.data_repo_tinydb.save_study(
        StudyDTO(
            path="somepath",
        )
    )
    run_with_mock.assert_not_called()

    # will use existing private workspace
    SlurmLauncher(
        config=launcher_config,
        callbacks=callbacks,
        event_bus=Mock(),
        retrieve_existing_jobs=True,
        cache=Mock(),
    )
    workspaces = [p for p in tmp_path.iterdir() if p.is_dir() and p.name != LOG_DIR_NAME]
    assert len(workspaces) == 1
    run_with_mock.assert_called()

    run_with_mock.reset_mock()
    # will create a new one since there is a lock on previous one
    SlurmLauncher(
        config=launcher_config,
        callbacks=callbacks,
        event_bus=Mock(),
        retrieve_existing_jobs=True,
        cache=Mock(),
    )
    workspaces = [p for p in tmp_path.iterdir() if p.is_dir() and p.name != LOG_DIR_NAME]
    assert len(workspaces) == 2
    run_with_mock.assert_not_called()
