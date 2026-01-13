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

"""
Matrix garbage collector service for non-Celery environments (e.g., desktop version).

This service runs as a background thread and periodically cleans unused matrices.
"""

import logging
import time

from typing_extensions import override

from antarest.core.interfaces.service import IService
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.maintenance.tasks.gc_variable_view import clean_variable_views
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


class MatrixGarbageCollector(IService):
    """
    Background service that periodically cleans unused matrices.

    This is used in non-Celery environments (desktop version) where
    we can't rely on Celery Beat for scheduling.
    """

    def __init__(self, matrix_service: MatrixService, sleeping_time: float, dry_run: bool, retention_time: int):
        self.matrix_service = matrix_service
        self.sleeping_time = sleeping_time
        self.dry_run = dry_run
        self.retention_time = retention_time

    @override
    def _loop(self) -> None:
        while True:
            try:
                clean_matrices(self.matrix_service, self.dry_run, self.retention_time)
                clean_variable_views(self.matrix_service, self.dry_run, self.retention_time)
            except Exception as e:
                logger.error("Error while cleaning matrices", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
