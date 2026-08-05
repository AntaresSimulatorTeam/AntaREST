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
from antarest.launcher.adapters.abstract_load import AbstractLoad
from antarest.launcher.model import LauncherLoad, LauncherLoadDTO
from antarest.launcher.repository import LauncherLoadRepository
from antarest.launcher.ssh_client import SlurmError

logger = logging.getLogger(__name__)


class LoadService:
    def __init__(
        self, config: Config, loads: dict[str, AbstractLoad], launcher_load_repository: LauncherLoadRepository
    ):
        self.config = config
        self.loads = loads
        self.launcher_cache_repository = launcher_load_repository

    def get_load(self, launcher_id: str | None) -> LauncherLoadDTO:
        """
        Get the load of the specified launcher.
        """
        if launcher_id is None:
            launcher_id = self.config.launcher.default

        load = self.loads.get(launcher_id)
        if load is None:
            raise InvalidConfigurationError(launcher_id)

        cached_load = self.launcher_cache_repository.get_launcher_load(launcher_id)
        if cached_load is not None and not self._is_outdated_load_data(cached_load):
            return cached_load.to_dto()

        logger.info("No valid cached load for launcher '%s', querying live", launcher_id)
        return load.get_load()

    def _is_outdated_load_data(self, load: LauncherLoad) -> bool:
        return load.date < current_time() - self.config.launcher.launcher_cache_validity_time

    def get_all_loads(self) -> dict[str, LauncherLoadDTO]:
        all_loads = {}
        for launcher_id, load in self.loads.items():
            try:
                all_loads[launcher_id] = load.get_load()
            except SlurmError:
                logger.warning("Failed to query load for launcher '%s'", launcher_id)

        return all_loads
