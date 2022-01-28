import logging
import threading
import time
from os import listdir
from pathlib import Path
from typing import Set, List

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.repository import MatrixDataSetRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

logger = logging.getLogger(__name__)


class MatrixGarbageCollector:
    def __init__(
        self,
        config: Config,
        study_service: StudyService,
        matrix_service: MatrixService,
    ):
        self.saved_matrices_path: Path = config.storage.matrixstore
        self.managed_studies_path: Path = config.storage.workspaces[
            DEFAULT_WORKSPACE_NAME
        ].path
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.study_service: StudyService = study_service
        self.variant_study_service: VariantStudyService = (
            study_service.storage_service.variant_study_service
        )
        self.matrix_service = matrix_service
        self.dataset_repository: MatrixDataSetRepository = (
            matrix_service.repo_dataset
        )

    def _get_saved_matrices(self) -> Set[str]:
        logging.info("Getting all saved matrices")
        return {f.split(".")[0] for f in listdir(self.saved_matrices_path)}

    def _get_raw_studies_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in raw studies")
        return {
            f.name.split(".")[0]
            for f in self.managed_studies_path.rglob("*.link")
        }

    def _get_variant_studies_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in variant studies")
        command_blocks: List[CommandBlock] = db.session.query(
            CommandBlock
        ).all()
        variant_study_commands = [
            icommand
            for c in command_blocks
            for icommand in self.variant_study_service.command_factory.to_icommand(
                c.to_dto()
            )
        ]
        matrices = {
            matrix
            for command in variant_study_commands
            for matrix in command.get_inner_matrices()
        }
        return matrices

    def _get_datasets_matrices(self) -> Set[str]:
        logger.info("Getting all matrices used in datasets")
        matrix_set = set()
        datasets = self.dataset_repository.get_all_datasets()
        for dataset in datasets:
            matrices = dataset.matrices
            for matrix in matrices:
                matrix_set.add(matrix.id)
        return matrix_set

    def _get_used_matrices(self) -> Set[str]:
        """Return all matrices used in raw studies, variant studies and datasets"""
        raw_studies_matrices = self._get_raw_studies_matrices()
        variant_studies_matrices = self._get_variant_studies_matrices()
        datasets_matrices = self._get_datasets_matrices()
        return (
            raw_studies_matrices | variant_studies_matrices | datasets_matrices
        )

    def _delete_unused_saved_matrices(self, unused_matrices: Set[str]) -> None:
        """Delete all files with the name in unused_matrices"""
        logging.info("Deleting unused saved matrices:")
        for unused_matrix_id in unused_matrices:
            logging.info(f"Deleting {unused_matrix_id}")
            self.matrix_service.delete(unused_matrix_id)

    def _clean_matrices(self) -> None:
        """Delete all matrices that are not used anymore"""
        stopwatch = StopWatch()
        logger.info("Beginning of the cleaning process")
        saved_matrices = self._get_saved_matrices()
        used_matrices = self._get_used_matrices()
        unused_matrices = saved_matrices - used_matrices
        self._delete_unused_saved_matrices(unused_matrices=unused_matrices)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Finished cleaning matrices in {x}s")
        )

    def _loop(self) -> None:
        while True:
            self._clean_matrices()
            logging.info("Sleeping for 1 hour")

            time.sleep(3600)

    def start(self) -> None:
        self.thread.start()
