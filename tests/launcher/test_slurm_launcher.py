from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.common.config import Config, LauncherConfig, SlurmConfig
from antarest.launcher.business.slurm_launcher.slurm_launcher import (
    SlurmLauncher,
)


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

    slurm_launcher = SlurmLauncher(config=config, storage_service=Mock())

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

    slurm_launcher = SlurmLauncher(config=config, storage_service=Mock())

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
    slurm_launcher = SlurmLauncher(config=config, storage_service=Mock())
    directory_path = Path(tmp_path) / "directory"
    directory_path.mkdir()
    (directory_path / "file.txt").touch()

    slurm_launcher._delete_study(directory_path)

    assert not directory_path.exists()
