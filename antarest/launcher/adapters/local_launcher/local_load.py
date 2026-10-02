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

import os

from typing_extensions import override

from antarest.launcher.adapters.abstract_load import AbstractLoad
from antarest.launcher.model import LauncherLoadDTO, LauncherParametersDTO


class LocalLoad(AbstractLoad):
    def __init__(self) -> None:
        super().__init__()
        self.submitted_jobs: dict[str, LauncherParametersDTO] = {}
        self.supports_load_caching = False

    @override
    def get_load(self) -> LauncherLoadDTO:
        local_used_cpus = sum(params.nb_cpu or 1 for params in self.submitted_jobs.values())

        # The cluster load is approximated by the percentage of used CPUs.
        cluster_load_approx = min(100.0, 100 * local_used_cpus / (os.cpu_count() or 1))

        args = {
            "allocatedCpuRate": cluster_load_approx,
            "clusterLoadRate": cluster_load_approx,
            "nbQueuedJobs": 0,
            "launcherStatus": "SUCCESS",
        }
        return LauncherLoadDTO(**args)
