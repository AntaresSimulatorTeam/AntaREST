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
import time
from typing import Set

from typing_extensions import override

from antarest.blobstore.service import BlobService
from antarest.core.interfaces.service import IService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch

logger = logging.getLogger(__name__)


class BlobGarbageCollector(IService):
    def __init__(self, blob_service: BlobService, sleeping_time: float, dry_run: bool):
        self.blob_service = blob_service
        self.sleeping_time = sleeping_time
        self.dry_run = dry_run

    def _delete_unused_saved_blobs(self, unused_blobs: Set[str]) -> None:
        """Delete all files with the name in unused_blobs"""
        logger.info("Deleting unused saved blobs:")
        for unused_blob_id in unused_blobs:
            logger.info(f"Blob {unused_blob_id} is set to be deleted")
            if not self.dry_run:
                logger.info(f"Deleting {unused_blob_id}")
                self.blob_service.delete(unused_blob_id)

    def clean_blobs(self) -> None:
        """Delete all blobs that are not used anymore"""
        stopwatch = StopWatch()
        logger.info("Beginning of the cleaning process")
        used_blobs = {blob.blob_id for blob in self.blob_service.get_used_blobs()}
        saved_blobs = self.blob_service.get_saved_blobs()
        unused_blobs = set(saved_blobs) - used_blobs

        if unused_blobs:
            self._delete_unused_saved_blobs(unused_blobs=unused_blobs)

        stopwatch.log_elapsed(lambda x: logger.info(f"Finished cleaning blobs in {x}s"))

    @override
    def _loop(self) -> None:
        while True:
            try:
                with db():
                    self.clean_blobs()
            except Exception as e:
                logger.error("Error while cleaning blobs", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
