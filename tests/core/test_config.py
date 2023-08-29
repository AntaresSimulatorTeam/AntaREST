from pathlib import Path
from unittest import mock

import pytest

from antarest.core.config import (
    Config,
    InvalidConfigurationError,
    LauncherConfig,
    LocalConfig,
    NbCoresConfig,
    SlurmConfig,
)
from tests.core.assets import ASSETS_DIR

LAUNCHER_CONFIG = {
    "default": "slurm",
    "local": {
        "binaries": {"860": Path("/bin/solver-860.exe")},
        "enable_nb_cores_detection": False,
        "nb_cores": {"min": 2, "default": 10, "max": 20},
    },
    "slurm": {
        "local_workspace": Path("/home/john/antares/workspace"),
        "username": "john",
        "hostname": "slurm-001",
        "port": 22,
        "private_key_file": Path("/home/john/.ssh/id_rsa"),
        "key_password": "password",
        "password": "password",
        "default_wait_time": 10,
        "default_time_limit": 20,
        "default_json_db_name": "antares.db",
        "slurm_script_path": "/path/to/slurm/launcher.sh",
        "max_cores": 32,
        "antares_versions_on_remote_server": ["860"],
        "enable_nb_cores_detection": False,
        "nb_cores": {"min": 1, "default": 34, "max": 36},
    },
    "batch_size": 100,
}


class TestNbCoresConfig:
    def test_init__default_values(self):
        config = NbCoresConfig()
        assert config.min == 1
        assert config.default == 22
        assert config.max == 24

    def test_init__invalid_values(self):
        with pytest.raises(ValueError):
            # default < min
            NbCoresConfig(min=2, default=1, max=24)
        with pytest.raises(ValueError):
            # default > max
            NbCoresConfig(min=1, default=25, max=24)
        with pytest.raises(ValueError):
            # min < 0
            NbCoresConfig(min=0, default=22, max=23)
        with pytest.raises(ValueError):
            # min > max
            NbCoresConfig(min=22, default=22, max=21)

    def test_to_json(self):
        config = NbCoresConfig()
        # ReactJs Material UI expects "min", "defaultValue" and "max" keys
        assert config.to_json() == {"min": 1, "defaultValue": 22, "max": 24}


class TestLocalConfig:
    def test_init__default_values(self):
        config = LocalConfig()
        assert config.binaries == {}, "binaries should be empty by default"
        assert config.enable_nb_cores_detection, "nb cores auto-detection should be enabled by default"
        assert config.nb_cores == NbCoresConfig()

    def test_from_dict(self):
        config = LocalConfig.from_dict(
            {
                "binaries": {"860": Path("/bin/solver-860.exe")},
                "enable_nb_cores_detection": False,
                "nb_cores": {"min": 2, "default": 10, "max": 20},
            }
        )
        assert config.binaries == {"860": Path("/bin/solver-860.exe")}
        assert not config.enable_nb_cores_detection
        assert config.nb_cores == NbCoresConfig(min=2, default=10, max=20)

    def test_from_dict__auto_detect(self):
        with mock.patch("multiprocessing.cpu_count", return_value=8):
            config = LocalConfig.from_dict(
                {
                    "binaries": {"860": Path("/bin/solver-860.exe")},
                    "enable_nb_cores_detection": True,
                }
            )
        assert config.binaries == {"860": Path("/bin/solver-860.exe")}
        assert config.enable_nb_cores_detection
        assert config.nb_cores == NbCoresConfig(min=1, default=6, max=8)


class TestSlurmConfig:
    def test_init__default_values(self):
        config = SlurmConfig()
        assert config.local_workspace == Path()
        assert config.username == ""
        assert config.hostname == ""
        assert config.port == 0
        assert config.private_key_file == Path()
        assert config.key_password == ""
        assert config.password == ""
        assert config.default_wait_time == 0
        assert config.default_time_limit == 0
        assert config.default_json_db_name == ""
        assert config.slurm_script_path == ""
        assert config.max_cores == 64
        assert config.antares_versions_on_remote_server == [], "solver versions should be empty by default"
        assert not config.enable_nb_cores_detection, "nb cores auto-detection shouldn't be enabled by default"
        assert config.nb_cores == NbCoresConfig()

    def test_from_dict(self):
        config = SlurmConfig.from_dict(
            {
                "local_workspace": Path("/home/john/antares/workspace"),
                "username": "john",
                "hostname": "slurm-001",
                "port": 22,
                "private_key_file": Path("/home/john/.ssh/id_rsa"),
                "key_password": "password",
                "password": "password",
                "default_wait_time": 10,
                "default_time_limit": 20,
                "default_json_db_name": "antares.db",
                "slurm_script_path": "/path/to/slurm/launcher.sh",
                "max_cores": 32,
                "antares_versions_on_remote_server": ["860"],
                "enable_nb_cores_detection": False,
                "nb_cores": {"min": 2, "default": 10, "max": 20},
            }
        )
        assert config.local_workspace == Path("/home/john/antares/workspace")
        assert config.username == "john"
        assert config.hostname == "slurm-001"
        assert config.port == 22
        assert config.private_key_file == Path("/home/john/.ssh/id_rsa")
        assert config.key_password == "password"
        assert config.password == "password"
        assert config.default_wait_time == 10
        assert config.default_time_limit == 20
        assert config.default_json_db_name == "antares.db"
        assert config.slurm_script_path == "/path/to/slurm/launcher.sh"
        assert config.max_cores == 32
        assert config.antares_versions_on_remote_server == ["860"]
        assert not config.enable_nb_cores_detection
        assert config.nb_cores == NbCoresConfig(min=2, default=10, max=20)

    def test_from_dict__default_n_cpu__backport(self):
        config = SlurmConfig.from_dict(
            {
                "local_workspace": Path("/home/john/antares/workspace"),
                "username": "john",
                "hostname": "slurm-001",
                "port": 22,
                "private_key_file": Path("/home/john/.ssh/id_rsa"),
                "key_password": "password",
                "password": "password",
                "default_wait_time": 10,
                "default_time_limit": 20,
                "default_json_db_name": "antares.db",
                "slurm_script_path": "/path/to/slurm/launcher.sh",
                "max_cores": 32,
                "antares_versions_on_remote_server": ["860"],
                "default_n_cpu": 15,
            }
        )
        assert config.nb_cores == NbCoresConfig(min=1, default=15, max=24)

    def test_from_dict__auto_detect(self):
        with pytest.raises(NotImplementedError):
            SlurmConfig.from_dict({"enable_nb_cores_detection": True})


class TestLauncherConfig:
    def test_init__default_values(self):
        config = LauncherConfig()
        assert config.default == "local", "default launcher should be local"
        assert config.local is None
        assert config.slurm is None
        assert config.batch_size == 9999

    def test_from_dict(self):
        config = LauncherConfig.from_dict(LAUNCHER_CONFIG)
        assert config.default == "slurm"
        assert config.local == LocalConfig(
            binaries={"860": Path("/bin/solver-860.exe")},
            enable_nb_cores_detection=False,
            nb_cores=NbCoresConfig(min=2, default=10, max=20),
        )
        assert config.slurm == SlurmConfig(
            local_workspace=Path("/home/john/antares/workspace"),
            username="john",
            hostname="slurm-001",
            port=22,
            private_key_file=Path("/home/john/.ssh/id_rsa"),
            key_password="password",
            password="password",
            default_wait_time=10,
            default_time_limit=20,
            default_json_db_name="antares.db",
            slurm_script_path="/path/to/slurm/launcher.sh",
            max_cores=32,
            antares_versions_on_remote_server=["860"],
            enable_nb_cores_detection=False,
            nb_cores=NbCoresConfig(min=1, default=34, max=36),
        )
        assert config.batch_size == 100

    def test_init__invalid_launcher(self):
        with pytest.raises(ValueError):
            LauncherConfig(default="invalid_launcher")

    def test_get_nb_cores__default(self):
        config = LauncherConfig.from_dict(LAUNCHER_CONFIG)
        # default == "slurm"
        assert config.get_nb_cores(launcher="default") == NbCoresConfig(min=1, default=34, max=36)

    def test_get_nb_cores__local(self):
        config = LauncherConfig.from_dict(LAUNCHER_CONFIG)
        assert config.get_nb_cores(launcher="local") == NbCoresConfig(min=2, default=10, max=20)

    def test_get_nb_cores__slurm(self):
        config = LauncherConfig.from_dict(LAUNCHER_CONFIG)
        assert config.get_nb_cores(launcher="slurm") == NbCoresConfig(min=1, default=34, max=36)

    def test_get_nb_cores__invalid_configuration(self):
        config = LauncherConfig.from_dict(LAUNCHER_CONFIG)
        with pytest.raises(InvalidConfigurationError):
            config.get_nb_cores("invalid_launcher")
        config = LauncherConfig.from_dict({})
        with pytest.raises(InvalidConfigurationError):
            config.get_nb_cores("slurm")


class TestConfig:
    @pytest.mark.parametrize("config_name", ["application-2.14.yaml", "application-2.15.yaml"])
    def test_from_yaml_file(self, config_name: str) -> None:
        yaml_path = ASSETS_DIR.joinpath("config", config_name)
        config = Config.from_yaml_file(yaml_path)
        assert config.security.admin_pwd == ""
        assert config.storage.workspaces["default"].path == Path("/home/john/antares_data/internal_studies")
        assert not config.logging.json
        assert config.logging.level == "INFO"
