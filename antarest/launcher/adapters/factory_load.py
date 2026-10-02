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

import logging

from antarest.core.config import Config, LocalConfig, SlurmConfig
from antarest.launcher.adapters.abstract_load import AbstractLoad
from antarest.launcher.adapters.local_launcher.local_load import LocalLoad
from antarest.launcher.adapters.slurm_launcher.slurm_load import SlurmLoad

logger = logging.getLogger(__name__)


def build_loads(config: Config) -> dict[str, AbstractLoad]:
    """
    Build the `AbstractLoad` objects used to query launcher loads, purely from configuration.

    Unlike `FactoryLauncher.build_launcher`, this doesn't require callbacks, an event bus, a
    cache or a study service: querying a launcher's load never needs any of those. This makes
    `AbstractLoad` instances cheap to build in any process (e.g. a celery worker) without having
    to construct a full `AbstractLauncher` (and its dependencies) just to read its load.
    """
    dict_loads: dict[str, AbstractLoad] = {}
    for cfg in config.launcher.configs or []:
        if isinstance(cfg, SlurmConfig):
            dict_loads[cfg.id] = SlurmLoad(cfg)
        elif isinstance(cfg, LocalConfig):
            dict_loads[cfg.id] = LocalLoad()

    return dict_loads
