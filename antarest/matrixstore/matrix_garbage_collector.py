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
from os import listdir
from pathlib import Path
from typing import TYPE_CHECKING, Set

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch

if TYPE_CHECKING:
    from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


class MatrixGarbageCollector(IService):
    def __init__(
        self,
        config: Config,
        matrix_service: "MatrixService",
    ):
        super(MatrixGarbageCollector, self).__init__()
        self.saved_matrices_path: Path = config.storage.matrixstore
        self.matrix_service = matrix_service
        self.sleeping_time = config.storage.matrix_gc_sleeping_time
        self.dry_run = config.storage.matrix_gc_dry_run

    def _get_saved_matrices(self) -> Set[str]:
        logger.info("Getting all saved matrices")
        return {f.split(".")[0] for f in listdir(self.saved_matrices_path)}

    def _delete_unused_saved_matrices(self, unused_matrices: Set[str]) -> None:
        """Delete all files with the name in unused_matrices"""
        logger.info("Deleting unused saved matrices:")
        for unused_matrix_id in unused_matrices:
            logger.info(f"Matrix {unused_matrix_id} is set to be deleted")
            if not self.dry_run:
                logger.info(f"Deleting {unused_matrix_id}")
                self.matrix_service.delete(unused_matrix_id)

    def _clean_matrices(self) -> None:
        """Delete all matrices that are not used anymore"""
        stopwatch = StopWatch()
        logger.info("Beginning of the cleaning process")
        saved_matrices = self._get_saved_matrices()
        used_matrices = self.matrix_service.get_used_matrices()
        unused_matrices = saved_matrices - used_matrices
        self._delete_unused_saved_matrices(unused_matrices=unused_matrices)
        stopwatch.log_elapsed(lambda x: logger.info(f"Finished cleaning matrices in {x}s"))

    @override
    def _loop(self) -> None:
        while True:
            try:
                with db():
                    self._clean_matrices()
            except Exception as e:
                logger.error("Error while cleaning matrices", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
