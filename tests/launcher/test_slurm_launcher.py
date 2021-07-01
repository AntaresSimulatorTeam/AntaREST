from pathlib import Path
from unittest.mock import Mock, ANY

import pytest
from sqlalchemy import create_engine

from antarest.common.config import Config, LauncherConfig, SlurmConfig
from antarest.common.persistence import Base
from antarest.common.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)
from antarest.launcher.model import JobStatus


@pytest.mark.unit_test
def test_init_slurm_launcher_arguments():
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                default_wait_time=42,
                default_time_limit=43,
                default_n_cpu=44,
                local_workspace=Path("local_workspace"),
            )
        )
    )

    slurm_launcher = SlurmLauncher(
        config=config, storage_service=Mock(), event_bus=Mock()
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
def test_init_slurm_launcher_parameters():
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                local_workspace=Path("local_workspace"),
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
        config=config, storage_service=Mock(), event_bus=Mock()
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
    assert main_parameters.default_ssh_dict_from_embedded_json == {
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
    config = Mock()
    config.launcher.slurm.local_workspace = Path(tmp_path)
    slurm_launcher = SlurmLauncher(
        config=config, storage_service=Mock(), event_bus=Mock()
    )
    directory_path = Path(tmp_path) / "directory"
    directory_path.mkdir()
    (directory_path / "file.txt").touch()

    slurm_launcher._delete_study(directory_path)

    assert not directory_path.exists()


@pytest.mark.unit_test
def test_run_study():
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                local_workspace=Path("local_workspace"),
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

    storage_service = Mock()
    slurm_launcher = SlurmLauncher(
        config=config, storage_service=storage_service, event_bus=Mock()
    )

    study_uuid = "study_uuid"
    params = Mock()
    argument = Mock()
    argument.studies_in = "studies_in"
    slurm_launcher._init_launcher_arguments = Mock(return_value=argument)
    slurm_launcher._init_launcher_parameters = Mock()
    slurm_launcher._clean_local_workspace = Mock()
    slurm_launcher._callback = Mock()
    slurm_launcher.start = Mock()
    slurm_launcher._delete_study = Mock()

    slurm_launcher.run_study(study_uuid, version="42", params=params)

    slurm_launcher._init_launcher_arguments.assert_called_once()
    slurm_launcher._init_launcher_parameters.assert_called_once()
    slurm_launcher._clean_local_workspace.assert_called_once()
    storage_service.export_study_flat.assert_called_once()
    slurm_launcher._callback.assert_called_once_with(ANY, JobStatus.RUNNING)
    slurm_launcher.start.assert_called_once()
    slurm_launcher._delete_study.assert_called_once()


@pytest.mark.unit_test
def test_check_state():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    config = Config(
        launcher=LauncherConfig(
            slurm=SlurmConfig(
                local_workspace=Path("local_workspace"),
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

    storage_service = Mock()
    slurm_launcher = SlurmLauncher(
        config=config, storage_service=storage_service, event_bus=Mock()
    )
    slurm_launcher._callback = Mock()
    slurm_launcher._import_study_output = Mock()
    slurm_launcher._delete_study = Mock()
    slurm_launcher.stop = Mock()

    study1 = Mock()
    study1.finished = True
    study1.name = "study1"
    slurm_launcher.job_id_to_study_id["study1"] = "job_id1"

    study2 = Mock()
    study2.finished = True
    study2.name = "study2"
    slurm_launcher.job_id_to_study_id["study2"] = "job_id2"

    data_repo_tinydb = Mock()
    data_repo_tinydb.get_list_of_studies = Mock(return_value=[study1, study2])
    data_repo_tinydb.remove_study = Mock()

    slurm_launcher._check_studies_state(
        arguments=Mock(),
        antares_launcher_parameters=Mock(),
        data_repo_tinydb=data_repo_tinydb,
    )

    assert slurm_launcher._callback.call_count == 2
    assert slurm_launcher._import_study_output.call_count == 2
    assert slurm_launcher._delete_study.call_count == 2
    assert data_repo_tinydb.remove_study.call_count == 2
    slurm_launcher.stop.assert_called_once()
