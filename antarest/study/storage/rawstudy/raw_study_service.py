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
from pathlib import Path
from typing import BinaryIO

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import RawStudy, StorageMode, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract.abstract_storage_service import AbstractStorageService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_database_storage import RawDataBaseStudyStorage
from antarest.study.storage.rawstudy.raw_file_study_storage import RawFileStudyStorage
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider

logger = logging.getLogger(__name__)


class RawStudyService(AbstractStorageService):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        cache: ICache,
        matrix_service: ISimpleMatrixService,
        raw_file_study_storage: RawFileStudyStorage,
        raw_database_study_storage: RawDataBaseStudyStorage,
    ):

        super().__init__(config=config, cache=cache)

        self.study_factory = study_factory
        self._matrix_service = matrix_service
        self._storage_mapping = {
            StorageMode.DATABASE: raw_database_study_storage,
            StorageMode.FILESYSTEM: raw_file_study_storage,
        }
        RawStudyMatrixUsageProvider(StudyMetadataRepository(cache_service=cache), matrix_service=self._matrix_service)

    def update_from_raw_metadata(self, study: Study) -> None:
        self._storage_mapping[study.storage_mode].update_from_raw_metadata(study, fallback_on_default=True)

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        return self._storage_mapping[study.storage_mode].update_name_and_version_from_raw_meta(study)

    def import_study(self, metadata: RawStudy, stream: BinaryIO) -> RawStudy:
        """
        Import study in the directory of the study.

        Args:
            metadata: study information.
            stream: binary content of the study compressed in ZIP or 7z format.

        Returns:
            Updated study information.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        study_path = Path(metadata.path)
        self._extract_and_setup(metadata, study_path, stream)
        return metadata
