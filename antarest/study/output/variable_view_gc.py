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
import time

from typing_extensions import override

from antarest.core.interfaces.service import IService
from antarest.maintenance.tasks.gc_variable_view import clean_variable_views

logger = logging.getLogger(__name__)


class VariableViewGarbageCollector(IService):
    """
    Background service that periodically cleans unused variable views.
    This is used in non-Celery environments (desktop version and self-hosted) where
    we can't rely on Celery.
    """

    def __init__(self, sleeping_time: float, dry_run: bool, retention_time: int):
        self.sleeping_time = sleeping_time
        self.dry_run = dry_run
        self.retention_time = retention_time

    @override
    def _loop(self) -> None:
        while True:
            try:
                clean_variable_views(self.dry_run, self.retention_time)
            except Exception as e:
                logger.error("Error while cleaning variable views", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
