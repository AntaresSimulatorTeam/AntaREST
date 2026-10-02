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

from pathlib import Path

from typing_extensions import override

from antarest.core.config import SlurmConfig
from antarest.launcher.adapters.abstract_load import AbstractLoad
from antarest.launcher.model import LauncherLoadDTO
from antarest.launcher.ssh_client import calculates_slurm_load
from antarest.launcher.ssh_config import SSHConfigDTO


class SlurmLoad(AbstractLoad):
    def __init__(self, config: SlurmConfig):
        super().__init__()
        self.slurm_config = config

    @override
    def get_load(self) -> LauncherLoadDTO:
        ssh_config = SSHConfigDTO(
            config_path=Path(),
            username=self.slurm_config.username,
            hostname=self.slurm_config.hostname,
            port=self.slurm_config.port,
            private_key_file=self.slurm_config.private_key_file,
            key_password=self.slurm_config.key_password,
            password=self.slurm_config.password,
        )
        partition = self.slurm_config.partition
        allocated_cpus, cluster_load, queued_jobs = calculates_slurm_load(ssh_config, partition)
        args = {
            "allocatedCpuRate": allocated_cpus,
            "clusterLoadRate": cluster_load,
            "nbQueuedJobs": queued_jobs,
            "launcherStatus": "SUCCESS",
        }
        return LauncherLoadDTO(**args)
