# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from pathlib import Path
from typing import Dict, Union

import pytest

from antarest.core.config import Config, InternalMatrixFormat, StorageConfig


@pytest.fixture
def storage_config_default() -> Dict[str, Union[str, int]]:
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
        "auto_archive_max_parallel": 10,
        "snapshot_retention_days": 14,
        "matrixstore_format": "tsv",
    }


def test_storage_config_from_dict(storage_config_default: Dict[str, Union[str, int]]):
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

    config = StorageConfig.from_dict(data)

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
    assert config.auto_archive_max_parallel == 10
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
            False,  # multuple workspaces allowed when desktop_mode is False
        ),
        (
            {
                "workspace1": {"path": "./workspace1"},
                "workspace2": {"path": "./workspace2"},
            },
            True,
            True,  # multuple workspace not allowed when desktop_mode is True
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
def test_storage_config_from_dict_validation_errors(storage_config_default, workspaces, desktop_mode, should_raise):
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
            Config.from_dict(config_data)
    else:
        Config.from_dict(config_data)
