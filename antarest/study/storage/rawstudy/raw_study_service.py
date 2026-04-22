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
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import RawStudy, StorageMode, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract.abstract_service import AbstractService
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.file_study_storage import FileStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class RawStudyService(AbstractService):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(self, config: Config, study_factory: StudyFactory, cache: ICache, command_context: CommandContext):

        super().__init__(cache, config)

        self.study_factory = study_factory
        self._matrix_service = command_context.matrix_service
        self._storage_mapping: dict[StorageMode, IStudyStorage] = {
            StorageMode.DATABASE: FileStudyStorage(cache, config, command_context, study_factory),
            StorageMode.FILESYSTEM: DatabaseStudyStorage(
                config=config,
                matrix_service=self._matrix_service,
                generator_matrix_constants=command_context.generator_matrix_constants,
            ),
        }
        RawStudyMatrixUsageProvider(StudyMetadataRepository(cache_service=cache), matrix_service=self._matrix_service)
        self.cache = cache

    def archive(self, study: Study) -> None:
        raise NotImplementedError()

    @override
    def unarchive(self, study: Study) -> None:
        raise NotImplementedError()

    @override
    def copy(self, src_study: Study, dest_name: str, groups: list[str], destination_folder: PurePosixPath) -> Study:
        self._check_study_exists(src_study)
        return self._storage_mapping[src_study.storage_mode].copy(src_study, dest_name, groups, destination_folder)

    @override
    def get_study_dao(self, study: Study) -> StudyDao:
        return self._storage_mapping[study.storage_mode].get_dao(study)

    @override
    def export_study_flat(self, study: Study, dst_path: Path) -> None:
        raise NotImplementedError()

    ##########################
    # Specific methods
    ##########################

    def normalize_study(self, study: Study) -> None:
        self._storage_mapping[study.storage_mode].normalize_study(study)

    def update_from_raw_metadata(self, study: RawStudy) -> None:
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
        return self._storage_mapping[metadata.storage_mode].import_study(metadata, stream)

    def denormalize_study(self, study: Study) -> None:
        raise NotImplementedError()
