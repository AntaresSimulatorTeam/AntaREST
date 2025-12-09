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

from antarest.core.interfaces.service import IService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch, current_time
from antarest.matrixstore.service import MatrixService

logger = logging.getLogger(__name__)


class MatrixGarbageCollector(IService):
    def __init__(self, matrix_service: MatrixService, sleeping_time: float, dry_run: bool, retention_time: int):
        self.matrix_service = matrix_service
        self.sleeping_time = sleeping_time
        self.dry_run = dry_run
        self.retention_time = retention_time

    def _delete_unused_saved_matrices(self, unused_matrices: Set[str]) -> None:
        """Delete all files with the name in unused_matrices"""
        logger.info("Deleting unused saved matrices:")
        for unused_matrix_id in unused_matrices:
            logger.info(f"Matrix {unused_matrix_id} is set to be deleted")
            if not self.dry_run:
                logger.info(f"Deleting {unused_matrix_id}")
                self.matrix_service.delete(unused_matrix_id)

    def clean_matrices(self) -> None:
        """Delete all matrices that are not used anymore"""
        stopwatch = StopWatch()
        logger.info("Beginning of the cleaning process")
        used_matrices = {matrix.matrix_id for matrix in self.matrix_service.get_used_matrices()}
        all_existing_matrices = self.matrix_service.get_matrices()
        saved_matrices = {matrix.id: matrix.created_at for matrix in all_existing_matrices}
        unused_matrices = set(saved_matrices) - used_matrices

        if unused_matrices:
            # Compare for each matrix, its lifetime duration to the `retention_time` value.
            # If it's more, remove the matrix. Otherwise, pass.
            matrices_to_remove = set()
            now = current_time()
            for matrix in unused_matrices:
                matrix_lifetime = (now - saved_matrices[matrix]).total_seconds()
                if matrix_lifetime >= self.retention_time:
                    matrices_to_remove.add(matrix)

            self._delete_unused_saved_matrices(unused_matrices=matrices_to_remove)

        stopwatch.log_elapsed(lambda x: logger.info(f"Finished cleaning matrices in {x}s"))

    @override
    def _loop(self) -> None:
        while True:
            try:
                with db():
                    self.clean_matrices()
            except Exception as e:
                logger.error("Error while cleaning matrices", exc_info=e)
            logger.info(f"Sleeping for {self.sleeping_time}s")
            time.sleep(self.sleeping_time)
