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

from antarest.core.config import Config, InvalidConfigurationError
from antarest.core.utils.utils import current_time
from antarest.launcher.adapters.abstractlauncher import AbstractLauncher
from antarest.launcher.model import LauncherLoad, LauncherLoadDTO
from antarest.launcher.repository import LauncherLoadRepository
from antarest.launcher.ssh_client import SlurmError

logger = logging.getLogger(__name__)


class LoadService:
    def __init__(
        self, config: Config, launchers: dict[str, AbstractLauncher], launcher_load_repository: LauncherLoadRepository
    ):
        self.config = config
        self.launchers = launchers
        self.launcher_cache_repository = launcher_load_repository

    def get_load(self, launcher_id: str | None) -> LauncherLoadDTO:
        """
        Get the load of the specified launcher.
        """
        if launcher_id is None:
            launcher_id = self.config.launcher.default

        launcher = self.launchers.get(launcher_id)
        if launcher is None:
            raise InvalidConfigurationError(launcher_id)

        load = self.launcher_cache_repository.get_launcher_load(launcher_id)
        if load is not None and not self._is_outdated_load_data(load):
            return load.to_dto()

        logger.info("No valid cached load for launcher '%s', querying live", launcher_id)
        return launcher.get_load()

    def _is_outdated_load_data(self, load: LauncherLoad) -> bool:
        return load.date < current_time() - self.config.launcher.launcher_cache_validity_time

    def get_all_loads(self) -> dict[str, LauncherLoadDTO]:
        all_loads = {}
        for launcher_id, launcher in self.launchers.items():
            try:
                all_loads[launcher_id] = launcher.get_load()
            except SlurmError:
                logger.warning("Failed to query load for launcher '%s'", launcher_id)

        return all_loads
