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
import re
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from antares.study.version import SolverVersion

from antarest.core.config import (
    Config,
    InternalMatrixFormat,
    LocalConfig,
    OutputStorageConfig,
    SlurmConfig,
    StorageConfig,
)


@pytest.fixture
def storage_config_default() -> dict[str, Any]:
    return {
        "matrixstore": "./custom_matrixstore",
        "archive_dir": "./custom_archives",
        "tmp_dir": "./custom_tmp",
        "allow_deletion": True,
        "watcher_lock": False,
        "watcher_lock_delay": 20,
        "download_default_expiration_timeout_minutes": 2880,
        "matrix_gc_sleeping_time": 7200,
        "matrix_gc_dry_run": True,
        "auto_archive_threshold_days": 120,
        "auto_archive_dry_run": True,
        "auto_archive_sleeping_time": 7200,
        "snapshot_retention_days": 14,
        "matrixstore_format": "tsv",
    }


def test_storage_config_from_dict(storage_config_default: dict[str, Any]) -> None:
    data = {
        **storage_config_default,
        "workspaces": {
            "workspace1": {
                "path": "./workspace1",
            },
            "workspace2": {
                "path": "./workspace2",
            },
        },
    }

    config = StorageConfig.model_validate(data)

    assert config.matrixstore == Path("./custom_matrixstore")
    assert config.archive_dir == Path("./custom_archives")
    assert config.tmp_dir == Path("./custom_tmp")
    assert config.workspaces["workspace1"].path == Path("./workspace1")
    assert config.workspaces["workspace2"].path == Path("./workspace2")
    assert config.allow_deletion is True
    assert config.watcher_lock is False
    assert config.watcher_lock_delay == 20
    assert config.download_default_expiration_timeout_minutes == 2880
    assert config.matrix_gc_sleeping_time == 7200
    assert config.matrix_gc_dry_run is True
    assert config.auto_archive_threshold_days == 120
    assert config.auto_archive_dry_run is True
    assert config.auto_archive_sleeping_time == 7200
    assert config.snapshot_retention_days == 14
    assert config.matrixstore_format == InternalMatrixFormat.TSV


@pytest.mark.parametrize(
    "workspaces, desktop_mode, should_raise",
    [
        (
            {
                "workspace1": {"path": "./workspace1"},
                "workspace2": {"path": "./workspace2"},
            },
            False,
            False,  # multiple workspaces allowed when desktop_mode is False
        ),
        (
            {
                "workspace1": {"path": "./workspace1"},
                "workspace2": {"path": "./workspace2"},
            },
            True,
            True,  # multiple workspace not allowed when desktop_mode is True
        ),
        (
            {
                "default": {"path": "./workspace1"},
            },
            True,
            False,  # desktop_mode is True but only default is set
        ),
        (
            {
                "workspace1": {"path": "./a/workspace1"},
                "workspace2": {"path": "./a/"},
            },
            False,
            True,  # workspaces overlap, should raise
        ),
        (
            {
                "workspace1": {"path": "./a/"},
                "workspace2": {"path": "./a/workspace2"},
            },
            False,
            True,  # workspaces overlap the other way around, should raise
        ),
        (
            {
                "workspace1": {"path": "./a/"},
                "workspace2": {"path": "./a/"},
            },
            False,
            True,  # workspaces path is duplicate, should raise
        ),
    ],
)
def test_storage_config_from_dict_validation_errors(
    storage_config_default: dict[str, Any],
    workspaces: dict[str, Any],
    desktop_mode: bool,
    should_raise: bool,
) -> None:
    data = {
        **storage_config_default,
        "workspaces": workspaces,
    }

    config_data = {
        "storage": data,
        "desktop_mode": desktop_mode,
    }

    if should_raise:
        with pytest.raises(ValueError):
            Config.model_validate(config_data)
    else:
        Config.model_validate(config_data)


def test_storage_config_from_dict_desktop_mode_true(storage_config_default: dict[str, Any]) -> None:
    data = {
        **storage_config_default,
        "workspaces": {
            "default": {
                "path": "./default_workspace",
            },
        },
    }

    config = Config.model_validate({"storage": data, "desktop_mode": True})

    assert "local" in config.storage.workspaces or "C:\\" in config.storage.workspaces


def test_storage_config_from_dict_auto_archive() -> None:
    data = {
        "auto_archive_sleeping_time": 3600,
        "auto_archive_cron": "* * * * *",
    }

    with pytest.raises(ValueError):
        StorageConfig.model_validate(data)


def test_launcher_config_solver_versions(tmp_path: Path) -> None:
    """
    Test that the launcher configuration correctly parses solver versions written in different formats.
    """
    data = {
        "launcher": {
            "default": "local",
            "launchers": [
                {"id": "local", "name": "local", "type": "local", "binaries": {"880": "", "9.2": "", "10.0": ""}},
                {
                    "id": "slurm",
                    "name": "slurm",
                    "type": "slurm",
                    "antares_versions_on_remote_server": ["8", "880", "9.2", "10.0"],
                },
            ],
        }
    }

    config_path = tmp_path / "config.yaml"
    with config_path.open(mode="w", encoding="utf-8") as fd:
        yaml.dump(data, fd)
    config = Config.from_yaml_file(config_path)

    # Local launcher
    local_launcher = cast(LocalConfig, config.launcher.configs[0])
    assert sorted(local_launcher.binaries) == [
        SolverVersion.parse("880"),
        SolverVersion.parse("9.2"),
        SolverVersion.parse("10.0"),
    ]

    # Slurm launcher
    slurm_launcher = cast(SlurmConfig, config.launcher.configs[1])
    assert sorted(slurm_launcher.antares_versions_on_remote_server) == [
        SolverVersion.parse("8"),
        SolverVersion.parse("880"),
        SolverVersion.parse("9.2"),
        SolverVersion.parse("10.0"),
    ]


def test_output_storage_config_validation_errors() -> None:
    data = {"v2": {"enable": False}, "default_storage_type": "V2"}

    with pytest.raises(
        ValueError, match=re.escape("You cannot set v2 storage as your default storage and not enable it")
    ):
        OutputStorageConfig.model_validate(data)
