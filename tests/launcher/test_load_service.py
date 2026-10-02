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

import math
import os
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from antarest.core.config import (
    Config,
    LauncherConfig,
    LocalConfig,
    SlurmConfig,
    StorageConfig,
)
from antarest.core.utils.utils import current_time
from antarest.launcher.adapters.local_launcher.local_load import LocalLoad
from antarest.launcher.adapters.slurm_launcher.slurm_load import SlurmLoad
from antarest.launcher.load_service import LoadService
from antarest.launcher.model import (
    JobResult,
    LauncherLoad,
    LauncherLoadDTO,
)


class TestLoadService:
    tmp_path = Path("/tmp")
    config = Config(
        storage=StorageConfig(tmp_dir=tmp_path),
        launcher=LauncherConfig(default="local", configs=[LocalConfig(id="local", name="name")]),
    )

    @pytest.mark.parametrize(
        ["running_jobs", "expected_result", "default_launcher"],
        [
            pytest.param(
                [],
                {
                    "allocatedCpuRate": 0.0,
                    "clusterLoadRate": 0.0,
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "local",
                id="local_no_running_job",
            ),
            pytest.param(
                [
                    Mock(
                        spec=JobResult,
                        launcher="local",
                        launcher_params=None,
                    ),
                    Mock(
                        spec=JobResult,
                        launcher="local",
                        launcher_params='{"nb_cpu": 7}',
                    ),
                ],
                {
                    "allocatedCpuRate": min(100.0, 800 / (os.cpu_count() or 1)),
                    "clusterLoadRate": min(100.0, 800 / (os.cpu_count() or 1)),
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "local",
                id="local_with_running_jobs",
            ),
            pytest.param(
                [],
                {
                    "allocatedCpuRate": 0.0,
                    "clusterLoadRate": 0.0,
                    "nbQueuedJobs": 0,
                    "launcherStatus": "SUCCESS",
                },
                "slurm",
                id="slurm launcher with no config",
                marks=pytest.mark.xfail(
                    reason="Configuration is not available for the slurm launcher",
                    raises=ValidationError,
                    strict=True,
                ),
            ),
        ],
    )
    def test_get_load(
        self,
        tmp_path: Path,
        running_jobs: list[JobResult],
        expected_result: dict[str, Any],
        default_launcher: str,
    ) -> None:

        config = Config(
            storage=StorageConfig(tmp_dir=tmp_path),
            launcher=LauncherConfig(default=default_launcher, configs=[LocalConfig(id="local", name="name")]),
        )

        load_dict = {}
        if default_launcher == "local":
            load_dict[default_launcher] = Mock()

        launcher_load_repository_mock = Mock()
        launcher_load_repository_mock.get_launcher_load.return_value.date = current_time()
        launcher_load_repository_mock.get_launcher_load.return_value.to_dto.return_value = (
            LauncherLoadDTO.model_validate(expected_result)
        )

        launcher_service = LoadService(
            config=config,
            launcher_load_repository=launcher_load_repository_mock,
            loads=load_dict,
        )

        launcher_expected_result = LauncherLoadDTO.model_validate(expected_result)
        actual_result = launcher_service.get_load(default_launcher)

        assert launcher_expected_result.launcher_status == actual_result.launcher_status
        assert launcher_expected_result.nb_queued_jobs == actual_result.nb_queued_jobs
        assert math.isclose(
            launcher_expected_result.cluster_load_rate,
            actual_result.cluster_load_rate,
        )
        assert math.isclose(
            launcher_expected_result.allocated_cpu_rate,
            actual_result.allocated_cpu_rate,
        )

    def test_get_load_is_updated_when_db_data_is_outdated(self, tmp_path: Path) -> None:
        outdated_cached_data = LauncherLoad(
            launcher_name="local",
            allocated_cpu_rate=10,
            cluster_load_rate=0,
            nb_queued_jobs=0,
            launcher_status="outdated status",
            date=current_time() - timedelta(days=1),
        )

        # The fresh DTO returned by the live launcher
        fresh_dto = LauncherLoadDTO(
            allocated_cpu_rate=50,
            cluster_load_rate=50,
            nb_queued_jobs=2,
            launcher_status="new status",
        )

        # Mock the live launcher adapter
        load_mock = Mock()
        load_mock.get_load.return_value = fresh_dto

        # Mock the DAO to return the outdated DB entry
        launcher_load_repository_mock = Mock()
        launcher_load_repository_mock.get_launcher_load.return_value = outdated_cached_data

        load_service = LoadService(
            config=self.config,
            launcher_load_repository=launcher_load_repository_mock,
            loads={"local": load_mock},
        )

        load = load_service.get_load("local")

        # The live launcher should have been called since the DB data was outdated
        load_mock.get_load.assert_called_once()
        assert load.launcher_status == "new status"
        assert load.allocated_cpu_rate == 50
        assert load.cluster_load_rate == 50
        assert load.nb_queued_jobs == 2

    def test_use_cached_launcher_data_when_not_outdated(self, tmp_path: Path) -> None:
        recent_cached_data = LauncherLoad(
            launcher_name="local",
            allocated_cpu_rate=10,
            cluster_load_rate=0,
            nb_queued_jobs=0,
            launcher_status="fresh status",
            date=current_time(),
        )

        load_mock = Mock()

        launcher_load_repository_mock = Mock()
        launcher_load_repository_mock.get_launcher_load.return_value = recent_cached_data

        launcher_service = LoadService(
            config=self.config,
            launcher_load_repository=launcher_load_repository_mock,
            loads={"local": load_mock},
        )

        load = launcher_service.get_load("local")

        load_mock.get_load.assert_not_called()
        assert load.launcher_status == "fresh status"
        assert load.allocated_cpu_rate == 10
        assert load.cluster_load_rate == 0
        assert load.nb_queued_jobs == 0

    @patch(
        "antarest.launcher.adapters.local_launcher.local_load.LocalLoad.get_load",
        new=Mock(
            return_value=LauncherLoadDTO(
                allocated_cpu_rate=10, cluster_load_rate=0, nb_queued_jobs=2, launcher_status="SUCCESS"
            )
        ),
    )
    def test_local_loads_are_not_cached(self) -> None:

        local_load = LocalLoad()

        launcher_load_repository_mock = Mock()
        launcher_load_repository_mock.get_launcher_load.raise_exception = True

        launcher_service = LoadService(
            config=self.config,
            launcher_load_repository=launcher_load_repository_mock,
            loads={"local": local_load},
        )

        # Testing the get_load method
        actual_load = launcher_service.get_load("local")

        launcher_load_repository_mock.get_launcher_load.assert_not_called()
        assert actual_load.launcher_status == "SUCCESS"
        assert actual_load.allocated_cpu_rate == 10
        assert actual_load.cluster_load_rate == 0
        assert actual_load.nb_queued_jobs == 2

        # Testing the get_cacheable_loads method
        actual_loads = launcher_service.get_cacheable_loads()

        launcher_load_repository_mock.get_launcher_load.assert_not_called()
        assert len(actual_loads) == 0

    @patch(
        "antarest.launcher.adapters.slurm_launcher.slurm_load.SlurmLoad.get_load",
        new=Mock(
            return_value=LauncherLoadDTO(
                allocated_cpu_rate=10, cluster_load_rate=0, nb_queued_jobs=2, launcher_status="SUCCESS"
            )
        ),
    )
    def test_slum_loads_are_cached(self) -> None:

        local_load = SlurmLoad(config=SlurmConfig(id="slurm_id", name="slurm"))

        launcher_load_repository_mock = Mock()
        launcher_load_repository_mock.get_launcher_load.return_value = LauncherLoad(
            launcher_name="slurm",
            date=current_time(),
            launcher_status="cached status",
            allocated_cpu_rate=20,
            cluster_load_rate=12,
            nb_queued_jobs=3,
        )

        launcher_service = LoadService(
            config=self.config,
            launcher_load_repository=launcher_load_repository_mock,
            loads={"slurm": local_load},
        )

        # Testing the get_load method
        actual_load = launcher_service.get_load("slurm")

        launcher_load_repository_mock.get_launcher_load.assert_called_once_with("slurm")
        assert actual_load.launcher_status == "cached status"
        assert actual_load.allocated_cpu_rate == 20
        assert actual_load.cluster_load_rate == 12
        assert actual_load.nb_queued_jobs == 3

        # Testing the get_cacheable_loads method
        actual_loads = launcher_service.get_cacheable_loads()

        assert len(actual_loads) == 1
