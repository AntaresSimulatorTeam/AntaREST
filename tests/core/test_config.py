# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import os.path
import tempfile
from pathlib import Path
from typing import Any, cast

import yaml
from antares.study.version import SolverVersion

from antarest.core.config import (
    CacheConfig,
    CeleryConfig,
    Config,
    DbConfig,
    LauncherConfig,
    LocalConfig,
    LoggingConfig,
    MetricsConfig,
    RedisConfig,
    SecurityConfig,
    ServerConfig,
    SlurmConfig,
    StorageConfig,
    TaskConfig,
)


class TestConfig:
    def test_config_is_fully_loaded(self) -> None:
        """
        Test that the launcher configuration correctly parses solver versions written in different formats.
        """
        data = {
            "server": {"worker_threadpool_size": 12, "services": ["watcher"]},
            "desktop_mode": False,
            "security": {"disabled": "true", "jwt": {"key": "my-secret-key"}},
            "storage": {
                "tmp_dir": "/tmp",
                "matrixstore": "/tmp/matrixstore",
                "archive_dir": "/tmp/archive",
                "workspaces": {
                    "default": {
                        "path": "/tmp/default_workspace",
                        "filter_in": ["filter_in_1", "filter_in_2"],
                        "filter_out": ["filter_out_1", "filter_out_2"],
                        "groups": ["group_1", "group_2"],
                    },
                    "studies": {"path": "/tmp/studies"},
                },
            },
            "launcher": {
                "default": "test_local",
                "launchers": [
                    {
                        "id": "test_local",
                        "name": "local",
                        "type": "local",
                        "binaries": {"880": "", "9.2": "", "10.0": ""},
                        "enable_nb_cores_detection": False,
                        "nb_cores": {"min": 10, "default": 100, "max": 1000},
                        "time_limit": {"min": 11, "default": 101, "max": 1001},
                        "xpress_dir": "/tmp/xpress_dir",
                        "local_workspace": "/tmp/local_workspace",
                    },
                    {
                        "id": "slurm_id",
                        "name": "slurm_name",
                        "type": "slurm",
                        "antares_versions_on_remote_server": ["8", "880", "9.2", "10.0"],
                        "local_workspace": "/tmp/slurm/local_workspace",
                        "username": "slurm_username",
                        "hostname": "slurm_hostname",
                        "port": 8888,
                        "private_key_file": "/tmp/slurm_key",
                        "key_password": "slurm_key_password",
                        "password": "slurm_password",
                        "default_wait_time": 60,
                        "nb_cores": {"min": 20, "default": 200, "max": 2000},
                        "default_json_db_name": "slurm_default_db_name",
                        "slurm_script_path": "slurm_script_path",
                        "partition": "slurm_partition",
                        "max_cores": 250,
                        "enable_nb_cores_detection": True,
                    },
                ],
            },
            "db": {
                "url": "db_url",
                "admin_url": "db_admin_url",
                "db_connect_timeout": 15,
                "pool_recycle": 3,
                "pool_pre_ping": True,
                "pool_use_null": True,
                "pool_max_overflow": 13,
                "pool_size": 20,
                "pool_use_lifo": True,
            },
            "logging": {"logfile": "/tmp/logfile", "json": True, "level": "DEBUG"},
            "debug": False,
            "resources_path": "/tmp/resources_path",
            "redis": {"host": "redis_host", "port": 1234, "password": "redis_password"},
            "cache": {"checker_delay": 0.5},
            "tasks": {
                "max_workers": 22,
                "remote_workers": [
                    {"name": "worker_1", "queues": ["queue_1_1", "queue_1_2"]},
                    {"name": "worker_2", "queues": ["queue_2_1", "queue_2_2"]},
                ],
            },
            "metrics": {"prometheus": {"multiprocess": True}},
            "celery": {"broker_url": "celery_url", "result_backend": "celery_backend", "result_expires": 60},
            "root_path": "/tmp/root_path",
            "api_prefix": "/api_prefix",
        }

        config_path = self.save_data_to_temporary_file(data)
        config = Config.from_yaml_file(config_path)

        assert config.desktop_mode is False
        assert config.debug is False
        assert config.resources_path == Path("/tmp/resources_path")

        self.check_server_config(config.server)
        self.check_security_config(config.security)
        self.check_storage_config(config.storage)
        self.check_launchers_config(config.launcher)
        self.check_db_config(config.db)
        self.check_logging_config(config.logging)
        self.check_redis_config(config.redis)
        self.check_cache_config(config.cache)
        self.check_task_config(config.tasks)
        self.check_metrics_config(config.metrics)
        self.check_celery_config(config.celery)
        assert config.root_path == "/tmp/root_path"
        assert config.api_prefix == "/api_prefix"

    def test_redis_config_loaded_in_celery_config(self) -> None:
        data = {
            "redis": {"host": "redis_host", "port": 1234, "password": "redis_password"},
        }

        config_path = self.save_data_to_temporary_file(data)

        config = Config.from_yaml_file(config_path)
        assert config.redis is not None
        assert config.celery is not None
        assert config.celery.broker_url == "redis://:redis_password@redis_host:1234/1"

    def save_data_to_temporary_file(self, data: dict[str, Any]) -> Path:
        tmp_path = tempfile.mkdtemp()
        config_path = Path(os.path.join(tmp_path, "config.yaml"))

        with config_path.open(mode="w", encoding="utf-8") as fd:
            yaml.dump(data, fd)
        return config_path

    def check_server_config(self, server_config: ServerConfig):
        assert server_config.worker_threadpool_size == 12
        assert server_config.services == ["watcher"]

    def check_security_config(self, security_config: SecurityConfig) -> None:
        assert security_config.disabled is True
        assert security_config.jwt_key == "my-secret-key"

    def check_storage_config(self, storage_config: StorageConfig) -> None:
        assert storage_config.tmp_dir == Path("/tmp")
        assert storage_config.matrixstore == Path("/tmp/matrixstore")
        assert storage_config.archive_dir == Path("/tmp/archive")

        workspaces = storage_config.workspaces
        assert workspaces["default"].path == Path("/tmp/default_workspace")
        assert workspaces["default"].filter_in == ["filter_in_1", "filter_in_2"]
        assert workspaces["default"].filter_out == ["filter_out_1", "filter_out_2"]
        assert workspaces["default"].groups == ["group_1", "group_2"]

        assert workspaces["studies"].path == Path("/tmp/studies")

    def check_launchers_config(self, launcher_config: LauncherConfig) -> None:
        assert launcher_config.default == "test_local"

        launchers = launcher_config.configs
        assert launchers is not None
        assert len(launchers) == 2

        local_launcher = cast(LocalConfig, launchers[0])
        slurm_launcher = cast(SlurmConfig, launchers[1])
        self.check_local_launcher(local_launcher)
        self.check_slurm_launcher(slurm_launcher)

    def check_local_launcher(self, local_launcher: LocalConfig) -> None:
        assert local_launcher.id == "test_local"
        assert local_launcher.name == "local"
        assert local_launcher.type == "local"
        assert local_launcher.binaries == {
            SolverVersion(major=8, minor=8, patch=0): Path("."),
            SolverVersion(major=9, minor=2, patch=0): Path("."),
            SolverVersion(major=10, minor=0, patch=0): Path("."),
        }
        assert local_launcher.enable_nb_cores_detection is False
        assert local_launcher.nb_cores.min == 10
        assert local_launcher.nb_cores.default == 100
        assert local_launcher.nb_cores.max == 1000

        assert local_launcher.time_limit.min == 11
        assert local_launcher.time_limit.default == 101
        assert local_launcher.time_limit.max == 1001

        assert local_launcher.xpress_dir == "/tmp/xpress_dir"
        assert local_launcher.local_workspace == Path("/tmp/local_workspace")

    def check_slurm_launcher(self, slurm_launcher):
        assert slurm_launcher.id == "slurm_id"
        assert slurm_launcher.name == "slurm_name"
        assert slurm_launcher.type == "slurm"
        assert slurm_launcher.antares_versions_on_remote_server == [
            SolverVersion(major=8, minor=0, patch=0),
            SolverVersion(major=8, minor=8, patch=0),
            SolverVersion(major=9, minor=2, patch=0),
            SolverVersion(major=10, minor=0, patch=0),
        ]
        assert slurm_launcher.local_workspace == Path("/tmp/slurm/local_workspace")
        assert slurm_launcher.username == "slurm_username"
        assert slurm_launcher.hostname == "slurm_hostname"
        assert slurm_launcher.port == 8888
        assert slurm_launcher.private_key_file == Path("/tmp/slurm_key")
        assert slurm_launcher.key_password == "slurm_key_password"
        assert slurm_launcher.password == "slurm_password"
        assert slurm_launcher.default_wait_time == 60
        assert slurm_launcher.nb_cores.min == 20
        assert slurm_launcher.nb_cores.default == 200
        assert slurm_launcher.nb_cores.max == 2000
        assert slurm_launcher.default_json_db_name == "slurm_default_db_name"
        assert slurm_launcher.slurm_script_path == "slurm_script_path"
        assert slurm_launcher.partition == "slurm_partition"
        assert slurm_launcher.max_cores == 250
        assert slurm_launcher.enable_nb_cores_detection is True

    def check_db_config(self, db_config: DbConfig) -> None:
        assert db_config.db_url == "db_url"
        assert db_config.db_admin_url == "db_admin_url"
        assert db_config.db_connect_timeout == 15
        assert db_config.pool_recycle == 3
        assert db_config.pool_pre_ping
        assert db_config.pool_use_null
        assert db_config.pool_max_overflow == 13
        assert db_config.pool_size == 20
        assert db_config.pool_use_lifo

    def check_logging_config(self, logging_config: LoggingConfig) -> None:
        assert logging_config.logfile == Path("/tmp/logfile")
        assert logging_config.json_format
        assert logging_config.level == "DEBUG"

    def check_redis_config(self, redis_config: RedisConfig | None) -> None:
        assert redis_config is not None
        assert redis_config.host == "redis_host"
        assert redis_config.port == 1234
        assert redis_config.password == "redis_password"

    def check_cache_config(self, cache_config: CacheConfig) -> None:
        assert cache_config.checker_delay == 0.5

    def check_task_config(self, task_config: TaskConfig) -> None:
        assert task_config.max_workers == 22
        workers = task_config.remote_workers
        assert workers[0].name == "worker_1"
        assert workers[0].queues == ["queue_1_1", "queue_1_2"]

        assert workers[1].name == "worker_2"
        assert workers[1].queues == ["queue_2_1", "queue_2_2"]

    def check_metrics_config(self, metrics_config: MetricsConfig) -> None:
        assert metrics_config.prometheus.multiprocess

    def check_celery_config(self, celery_config: CeleryConfig) -> None:
        assert celery_config.broker_url == "celery_url"
        assert celery_config.result_backend == "celery_backend"
        assert celery_config.result_expires == 60
