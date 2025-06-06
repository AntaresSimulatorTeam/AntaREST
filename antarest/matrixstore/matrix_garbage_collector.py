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
from typing import List, Set

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.matrixstore.repository import MatrixDataSetRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)


class MatrixGarbageCollector(IService):
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        matrix_service: MatrixService,
    ):
        super(MatrixGarbageCollector, self).__init__()
        self.saved_matrices_path: Path = config.storage.matrixstore
        self.managed_studies_path: Path = config.storage.workspaces[DEFAULT_WORKSPACE_NAME].path
        self.study_service: StudyService = study_service
        self.variant_study_service: VariantStudyService = study_service.storage_service.variant_study_service
        self.matrix_service = matrix_service
        self.dataset_repository: MatrixDataSetRepository = matrix_service.repo_dataset
        self.sleeping_time = config.storage.matrix_gc_sleeping_time
        self.matrix_constants = self.variant_study_service.command_factory.command_context.generator_matrix_constants
        self.dry_run = config.storage.matrix_gc_dry_run

    def _get_saved_matrices(self) -> Set[str]:
        logger.info("Getting all saved matrices")
        return {f.split(".")[0] for f in listdir(self.saved_matrices_path)}

    def _get_raw_studies_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in raw studies")
        return {
            matrix_id
            for matrix_id in [extract_matrix_id(f.read_text()) for f in self.managed_studies_path.rglob("*.link")]
            if matrix_id
        }

    def _get_variant_studies_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in variant studies")
        command_blocks: List[CommandBlock] = self.variant_study_service.repository.get_all_command_blocks()

        def transform_to_command(command_dto: CommandDTO, study_ref: str) -> List[ICommand]:
            try:
                return self.variant_study_service.command_factory.to_command(command_dto)
            except Exception as e:
                logger.warning(
                    f"Failed to parse command {command_dto} (from study {study_ref}) !",
                    exc_info=e,
                )
            return []

        variant_study_commands = [cmd for c in command_blocks for cmd in transform_to_command(c.to_dto(), c.study_id)]
        matrices = {matrix for command in variant_study_commands for matrix in command.get_inner_matrices()}
        return matrices

    def _get_datasets_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in datasets")
        datasets = self.dataset_repository.get_all_datasets()
        return {matrix.matrix_id for dataset in datasets for matrix in dataset.matrices}

    def _get_used_matrices(self) -> Set[str]:
        """Return all matrices used in raw studies, variant studies and datasets"""
        raw_studies_matrices = self._get_raw_studies_matrices()
        variant_studies_matrices = self._get_variant_studies_matrices()
        datasets_matrices = self._get_datasets_matrices()
        return (
            raw_studies_matrices
            | variant_studies_matrices
            | datasets_matrices
            | set(self.matrix_constants.hashes.values())
        )

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
