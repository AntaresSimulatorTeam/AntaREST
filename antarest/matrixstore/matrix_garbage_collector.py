import logging
import threading
from os import listdir
from pathlib import Path
from typing import Set

from antarest.core.config import Config
from antarest.core.exceptions import StudyTypeUnsupported
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.matrixstore.repository import MatrixDataSetRepository
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

logger = logging.getLogger(__name__)


class MatrixGarbageCollector:
    def __init__(self, config: Config, study_service: StudyService):
        self.saved_matrices_path: Path = config.storage.matrixstore
        self.managed_studies_path: Path = config.storage.workspaces[
            "default"
        ].path
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.study_service: StudyService = study_service
        self.variant_study_service: VariantStudyService = (
            study_service.storage_service.variant_study_service
        )
        self.dataset_repository: MatrixDataSetRepository = (
            MatrixDataSetRepository()
        )

    def _get_saved_matrices(self) -> Set[str]:
        logging.info("Getting all saved matrices")
        return {f.split(".")[0] for f in listdir(self.saved_matrices_path)}

    def _get_matrices_used_in_raw_studies(self) -> Set[str]:
        logger.info("Getting all matrices used in raw studies")
        return {
            f.name.split(".")[0]
            for f in self.managed_studies_path.rglob("*.link")
        }

    def _get_matrices_used_in_variant_studies(self) -> Set[str]:
        logger.info("Getting all matrices used in variant studies")
        params = RequestParameters(user=DEFAULT_ADMIN_USER)
        list_studies = self.study_service.get_studies_information(
            summary=True,
            managed=True,
            params=params,
        ).keys()
        variant_study_commands = []
        for study_id in list_studies:
            try:
                variant_study_commands += (
                    self.variant_study_service.get_icommands(
                        variant_study_id=study_id, params=params
                    )
                )
            except StudyTypeUnsupported:
                pass
        matrices = {
            matrix
            for command in variant_study_commands
            for matrix in command.get_inner_matrices()
        }
        return matrices

    def _get_matrices_used_in_datasets(self) -> Set[str]:
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
        raw_studies_matrices = self._get_matrices_used_in_raw_studies()
        variant_studies_matrices = self._get_matrices_used_in_variant_studies()
        datasets_matrices = self._get_matrices_used_in_datasets()
        return (
            raw_studies_matrices | variant_studies_matrices | datasets_matrices
        )

    def _delete_unused_saved_matrices(self, unused_matrices: Set[str]) -> None:
        """Delete all files with the name in unused_matrices"""
        logging.info("Deleting unused saved matrices:")
        for unused_matrix_name in unused_matrices:
            logging.info(f"\tDeleting {unused_matrix_name}")
            matrix_path = (
                self.saved_matrices_path / f"{unused_matrix_name}.txt"
            )
            matrix_path.unlink()

    def _clean_matrices(self) -> None:
        """Delete all matrices that are not used anymore"""
        saved_matrices = self._get_saved_matrices()
        used_matrices = self._get_used_matrices()
        unused_matrices = saved_matrices - used_matrices
        self._delete_unused_saved_matrices(unused_matrices=unused_matrices)
        logging.info("Finished cleaning matrices")

    def _loop(self) -> None:
        while True:
            self._clean_matrices()
            logging.info("Sleeping for 1 hour")
            import time

            time.sleep(3600)

    def start(self) -> None:
        self.thread.start()
