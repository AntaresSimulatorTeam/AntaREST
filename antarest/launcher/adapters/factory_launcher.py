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

import logging
from typing import Dict

from antarest.core.config import Config, LocalConfig, SlurmConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher, LauncherCallbacks
from antarest.launcher.adapters.local_launcher.local_launcher import LocalLauncher
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import SlurmLauncher

logger = logging.getLogger(__name__)


class FactoryLauncher:
    def build_launcher(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        cache: ICache,
    ) -> Dict[str, AbstractLauncher]:
        dict_launchers: Dict[str, AbstractLauncher] = dict()
        for cfg in config.launcher.configs or []:
            if isinstance(cfg, SlurmConfig):
                dict_launchers[cfg.id] = SlurmLauncher(
                    cfg,
                    callbacks,
                    event_bus,
                    cache,
                    retrieve_existing_jobs=True,
                )
            elif isinstance(cfg, LocalConfig):
                dict_launchers[cfg.id] = LocalLauncher(cfg, callbacks, event_bus, cache)

        return dict_launchers
