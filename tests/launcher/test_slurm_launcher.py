import os
import shutil
import uuid
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, ANY, patch

import pytest
from sqlalchemy import create_engine

from antareslauncher.data_repo.data_repo_tinydb import DataRepoTinydb
from antareslauncher.main import MainParameters
from antarest.core.config import Config, LauncherConfig, SlurmConfig
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.launcher.model import JobStatus
from antarest.study.model import StudyMetadataDTO, RawStudy


@pytest.fixture
def launcher_config(tmp_path: Path) -> Config:
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
    return config


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

    slurm_launcher = SlurmLauncher(
        config=config,
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
    )

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
    assert (
        Path(arguments.studies_in)
        == config.launcher.slurm.local_workspace / "STUDIES_IN"
    )
    assert (
        Path(arguments.output_dir)
        == config.launcher.slurm.local_workspace / "OUTPUT"
    )
    assert (
        Path(arguments.log_dir)
        == config.launcher.slurm.local_workspace / "LOGS"
    )


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

    slurm_launcher = SlurmLauncher(
        config=config,
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
    )

    main_parameters = slurm_launcher._init_launcher_parameters()
    assert main_parameters.json_dir == config.launcher.slurm.local_workspace
    assert (
        main_parameters.default_json_db_name
        == config.launcher.slurm.default_json_db_name
    )
    assert (
        main_parameters.slurm_script_path
        == config.launcher.slurm.slurm_script_path
    )
    assert (
        main_parameters.antares_versions_on_remote_server
        == config.launcher.slurm.antares_versions_on_remote_server
    )
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
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(local_workspace=Path(tmp_path))
        )
    )
    slurm_launcher = SlurmLauncher(
        config=config,
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
    )
    directory_path = Path(tmp_path) / "directory"
    directory_path.mkdir()
    (directory_path / "file.txt").touch()

    slurm_launcher._delete_study(directory_path)

    assert not directory_path.exists()


def test_extra_parameters(launcher_config: Config):
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
    )
    launcher_params = slurm_launcher._check_and_apply_launcher_params({})
    assert launcher_params.n_cpu == 1
    assert launcher_params.time_limit == 0
    assert not launcher_params.xpansion_mode
    assert not launcher_params.post_processing

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"nb_cpu": 12}
    )
    assert launcher_params.n_cpu == 12

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"nb_cpu": 48}
    )
    assert launcher_params.n_cpu == 1

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"time_limit": 999999999}
    )
    assert launcher_params.time_limit == 0

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"time_limit": 99999}
    )
    assert launcher_params.time_limit == 99999

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"xpansion": True}
    )
    assert launcher_params.xpansion_mode

    launcher_params = slurm_launcher._check_and_apply_launcher_params(
        {"post_processing": True}
    )
    assert launcher_params.post_processing


@pytest.mark.parametrize(
    "version,job_status", [(42, JobStatus.RUNNING), (99, JobStatus.FAILED)]
)
@pytest.mark.unit_test
def test_run_study(
    tmp_path: Path,
    launcher_config: Config,
    version: int,
    job_status: JobStatus,
):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    study_metadata_dto = Mock(spec=StudyMetadataDTO)
    study_metadata_dto.version = version
    storage_service = Mock()

    storage_service.get_study_information = Mock(
        return_value=study_metadata_dto
    )
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        study_service=storage_service,
        callbacks=Mock(),
        event_bus=Mock(),
    )

    study_uuid = "study_uuid"
    params = Mock()
    argument = Mock()
    argument.studies_in = "studies_in"
    slurm_launcher.launcher_args = argument
    slurm_launcher._clean_local_workspace = Mock()
    slurm_launcher.start = Mock()
    slurm_launcher._delete_study = Mock()

    slurm_launcher._run_study(
        study_uuid, str(uuid.uuid4()), None, params=params
    )

    #    slurm_launcher._clean_local_workspace.assert_called_once()
    storage_service.export_study_flat.assert_called_once()
    slurm_launcher.callbacks.update_status.assert_called_once_with(
        ANY, job_status, ANY, None
    )
    slurm_launcher.start.assert_called_once()
    if job_status == JobStatus.RUNNING:
        slurm_launcher._delete_study.assert_called_once()


@pytest.mark.unit_test
def test_check_state(tmp_path: Path, launcher_config: Config):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    storage_service = Mock()
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        study_service=storage_service,
        callbacks=Mock(),
        event_bus=Mock(),
    )
    slurm_launcher._import_study_output = Mock()
    slurm_launcher._delete_study = Mock()
    slurm_launcher.stop = Mock()

    study1 = Mock()
    study1.done = True
    study1.name = "study1"
    study1.with_error = False
    study1.job_log_dir = tmp_path / "study1"
    slurm_launcher.job_id_to_study_id["study1"] = "job_id1"

    study2 = Mock()
    study2.done = True
    study2.name = "study2"
    study2.with_error = True
    study2.job_log_dir = tmp_path / "study2"
    slurm_launcher.job_id_to_study_id["study2"] = "job_id2"

    data_repo_tinydb = Mock()
    data_repo_tinydb.get_list_of_studies = Mock(return_value=[study1, study2])
    data_repo_tinydb.remove_study = Mock()

    slurm_launcher.launcher_params = Mock()
    slurm_launcher.launcher_args = Mock()
    slurm_launcher.data_repo_tinydb = data_repo_tinydb

    slurm_launcher._check_studies_state()

    assert slurm_launcher.callbacks.update_status.call_count == 2
    assert slurm_launcher._import_study_output.call_count == 1
    assert slurm_launcher._delete_study.call_count == 2
    assert data_repo_tinydb.remove_study.call_count == 2
    slurm_launcher.stop.assert_called_once()


@pytest.mark.unit_test
def test_clean_local_workspace(tmp_path: Path, launcher_config: Config):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    storage_service = Mock()
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        study_service=storage_service,
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
    )

    (launcher_config.launcher.slurm.local_workspace / "machin.txt").touch()

    assert os.listdir(launcher_config.launcher.slurm.local_workspace)
    slurm_launcher._clean_local_workspace()
    assert not os.listdir(launcher_config.launcher.slurm.local_workspace)


@pytest.mark.unit_test
def test_import_study_output(launcher_config):
    slurm_launcher = SlurmLauncher(
        config=launcher_config,
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
    )
    slurm_launcher.job_id_to_study_id["1"] = "2"
    slurm_launcher.storage_service.import_output.return_value = "output"
    res = slurm_launcher._import_study_output("1")

    slurm_launcher.storage_service.import_output.assert_called_once_with(
        "2",
        launcher_config.launcher.slurm.local_workspace
        / "OUTPUT"
        / "1"
        / "output",
        params=ANY,
    )
    assert res == "output"

    link_dir = (
        launcher_config.launcher.slurm.local_workspace
        / "OUTPUT"
        / "1"
        / "input"
        / "links"
    )
    link_dir.mkdir(parents=True)
    link_file = link_dir / "something"
    link_file.write_text("hello")
    xpansion_dir = Path(
        launcher_config.launcher.slurm.local_workspace
        / "OUTPUT"
        / "1"
        / "user"
        / "expansion"
    )
    xpansion_dir.mkdir(parents=True)
    xpansion_test_file = xpansion_dir / "something_else"
    xpansion_test_file.write_text("world")
    output_dir = (
        launcher_config.launcher.slurm.local_workspace
        / "OUTPUT"
        / "1"
        / "output"
        / "output_name"
    )
    output_dir.mkdir(parents=True)
    slurm_launcher.storage_service.get_study.side_effect = [
        Mock(spec=RawStudy, version="800"),
        Mock(spec=RawStudy, version="700"),
    ]
    assert not (output_dir / "updated_links" / "something").exists()
    assert not (output_dir / "updated_links" / "something").exists()

    slurm_launcher._import_study_output("1", True)
    assert (output_dir / "updated_links" / "something").exists()
    assert (output_dir / "updated_links" / "something").read_text() == "hello"
    shutil.rmtree(output_dir / "updated_links")

    slurm_launcher._import_study_output("1", True)
    assert (output_dir / "results" / "something_else").exists()
    assert (output_dir / "results" / "something_else").read_text() == "world"


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
        study_service=Mock(),
        callbacks=Mock(),
        event_bus=Mock(),
        use_private_workspace=False,
    )
    slurm_launcher.data_repo_tinydb = data_repo_tinydb_mock

    slurm_launcher.kill_job(job_id=launch_id)

    launcher_arguments = Namespace(
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
        xpansion_mode=False,
    )
    launcher_parameters = MainParameters(
        json_dir=Path(tmp_path),
        default_json_db_name="default_json_db_name",
        slurm_script_path="slurm_script_path",
        antares_versions_on_remote_server=["42"],
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

    run_with_mock.assert_called_with(
        launcher_arguments, launcher_parameters, show_banner=False
    )
