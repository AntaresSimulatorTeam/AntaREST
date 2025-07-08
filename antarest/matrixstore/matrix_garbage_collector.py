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
from typing import Set, List

from pandas.core.interchange.dataframe_protocol import DataFrame
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.repository import MatrixDataSetRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


class MatrixGarbageCollector(IService):
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        matrix_service: MatrixService,
        matrices_usage_providers: list[IMatrixUsageProvider],
    ):
        super(MatrixGarbageCollector, self).__init__()
        self.saved_matrices_path: Path = config.storage.matrixstore
        self.variant_study_service: VariantStudyService = study_service.storage_service.variant_study_service
        self.matrix_service = matrix_service
        self.matrices_usage_providers = matrices_usage_providers
        self.dataset_repository: MatrixDataSetRepository = matrix_service.repo_dataset
        self.sleeping_time = config.storage.matrix_gc_sleeping_time
        self.matrix_constants = self.variant_study_service.command_factory.command_context.generator_matrix_constants
        self.dry_run = config.storage.matrix_gc_dry_run

    def _get_saved_matrices(self) -> Set[str]:
        logger.info("Getting all saved matrices")
        return {f.split(".")[0] for f in listdir(self.saved_matrices_path)}

    def _get_studies_matrices(self) -> List[DataFrame]:
        # A mettre dans RSM
        logger.info("Getting all matrices used in raw studies")

        return [
            self.matrix_service.get(matrix_reference.matrix_id)
            for provider in self.matrices_usage_providers
            for matrix_reference in provider.get_matrix_usage()
        ]

    def _get_datasets_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in datasets")
        datasets = self.dataset_repository.get_all_datasets()
        return {matrix.matrix_id for dataset in datasets for matrix in dataset.matrices}

    def _get_used_matrices(self) -> Set[str]:
        """Return all matrices used in raw studies, variant studies and datasets"""
        studies_matrices = self._get_studies_matrices()
        datasets_matrices = self._get_datasets_matrices()
        return studies_matrices | datasets_matrices | set(self.matrix_constants.hashes.values())

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
        used_matrices = self._get_used_matrices()
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
