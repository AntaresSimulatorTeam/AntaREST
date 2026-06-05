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
Blob garbage collector service for non-Celery environments (e.g., desktop version).

This service runs as a background thread and periodically cleans unused blobs.
"""

import logging
import time
from pathlib import Path

from typing_extensions import override

from antarest.blobstore.service import BlobService
from antarest.core.interfaces.service import IService
from antarest.maintenance.tasks.gc_blob import clean_blobs

logger = logging.getLogger(__name__)


class BlobGarbageCollector(IService):
    def __init__(self, blob_service: BlobService, sleeping_time: float, dry_run: bool, lock_folder: Path):
        self.blob_service = blob_service
        self.sleeping_time = sleeping_time
        self.dry_run = dry_run
        self.lock_folder = lock_folder

    @override
    def _loop(self) -> None:
        while True:
            try:
                clean_blobs(self.blob_service, self.dry_run, lock_folder=self.lock_folder)
            except Exception as e:
                logger.error("Error while cleaning blobs", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
