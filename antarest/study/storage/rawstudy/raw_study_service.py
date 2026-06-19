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
import shutil
from pathlib import Path

from antares.study.version import StudyVersion
from markupsafe import escape
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.archives import (
    archive_dir,
)
from antarest.core.utils.utils import StopWatch
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory, ResourcePaths
from antarest.study.model import RawStudy, StorageMode, Study, StudyMetadataCopy, StudyMetadataCreation
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract.abstract_study_service import AbstractStudyService
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.file_study_storage import FileStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import (
    get_disk_usage,
    is_managed,
    remove_from_cache,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class RawStudyService(AbstractStudyService):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        cache: ICache,
        command_context: CommandContext,
        repository: StudyMetadataRepository,
    ):

        super().__init__(cache, config)

        self.study_factory = study_factory
        self.repository = repository
        self._matrix_service = command_context.matrix_service
        generator_matrix_constants = command_context.generator_matrix_constants
        db_dao_factory = DatabaseStudyDaoFactory(self._matrix_service, generator_matrix_constants)
        fs_dao_factory = FileStudyDaoFactory(
            self._matrix_service,
            command_context.blob_service,
            generator_matrix_constants,
            study_factory,
            cache,
            self.get_study_paths,
        )
        self._study_dao_factories: dict[StorageMode, StudyFactoryDao] = {
            StorageMode.DATABASE: db_dao_factory,
            StorageMode.FILESYSTEM: fs_dao_factory,
        }
        self._file_study_storage = FileStudyStorage(config, repository, self._matrix_service, study_factory)
        self._database_study_storage = DatabaseStudyStorage(
            config, repository, self._matrix_service, db_dao_factory, fs_dao_factory
        )
        self._storage_mapping: dict[StorageMode, IStudyStorage] = {
            StorageMode.FILESYSTEM: self._file_study_storage,
            StorageMode.DATABASE: self._database_study_storage,
        }
        RawStudyMatrixUsageProvider(repository, self._matrix_service, self._storage_mapping)
        self.cache = cache

    @override
    def copy(self, src_study: Study, metadata: StudyMetadataCopy) -> RawStudy:
        return self._storage_mapping[src_study.storage_mode].copy(src_study, metadata)

    @override
    def get_study_dao(self, study: Study) -> StudyDao:
        return self._study_dao_factories[study.storage_mode].get_study_dao(study.id, is_managed(study))

    @override
    def export_study_flat(self, study: Study, dst_path: Path) -> None:
        self._storage_mapping[study.storage_mode].export_study(study, dst_path)

    ##########################
    # Specific methods
    ##########################

    def get_study_paths(self, study_id: str) -> ResourcePaths:
        study = self.repository.get(study_id)
        if not study:
            sanitized = str(escape(study_id))
            logger.warning("Study %s not found in metadata db", sanitized)
            raise StudyNotFoundError(study_id)
        return ResourcePaths(study_path=Path(study.path), output_path=None)

    def create_study_dao(self, study: RawStudy) -> None:
        metadata = StudyMetadataCreation(
            id=study.id,
            version=StudyVersion.parse(study.version),
            managed=is_managed(study),
            name=study.name,
            author=study.author,
            editor=study.editor,
            created_at=study.created_at,
            updated_at=study.updated_at,
        )
        self._study_dao_factories[study.storage_mode].create_study_dao(metadata)

    def get_disk_usage(self, study: Study) -> int:
        if study.archived:
            return get_disk_usage(self.find_archive_path(study))
        return self._storage_mapping[study.storage_mode].get_disk_usage(study)

    def archive(self, study: RawStudy) -> None:
        dst_path = self._config.storage.tmp_dir / f"archive_{study.id}"
        self._storage_mapping[study.storage_mode].write_study_for_archive(study, dst_path)

        archive_format = self._config.storage.archive_format
        archive_path = self._config.storage.archive_dir.joinpath(f"{study.id}{archive_format}")

        try:
            stopwatch = StopWatch()
            archive_dir(dst_path, archive_path, False, archive_format)
            logger.info(f"Study {study.id} exported ({archive_path.suffix} format) in {stopwatch}s")
        except Exception as e:
            logger.warning(f"Failed to archive study {study.id}", exc_info=e)
            archive_path.unlink(missing_ok=True)

        else:
            # Remove the source study data if everything went well
            self._storage_mapping[study.storage_mode].remove_study_data(study)
            remove_from_cache(cache=self.cache, root_id=study.id)
            self.cache.invalidate(study.id)

        finally:
            # Remove the temporary folder
            shutil.rmtree(dst_path, ignore_errors=True)

    def unarchive(self, study: RawStudy) -> None:
        archive_path = self.find_archive_path(study)
        self._storage_mapping[study.storage_mode].unarchive(study, archive_path)
        archive_path.unlink()

    def normalize_study(self, study: Study) -> None:
        self._storage_mapping[study.storage_mode].normalize_study(study)

    def update_from_raw_metadata(self, study: RawStudy) -> None:
        self._file_study_storage.update_from_raw_metadata(study)

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        return self._file_study_storage.update_name_and_version_from_raw_meta(study)

    def import_study(self, study: RawStudy, study_dir: Path) -> RawStudy:
        """
        Import study in the directory of the study.

        Args:
            study: study information.
            study_dir: Temporary folder containing the study unarchived

        Returns:
            Updated study information.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        self._storage_mapping[study.storage_mode].import_study(study, study_dir)
        return study

    def upgrade_study(self, study: Study, version: StudyVersion) -> None:
        self._storage_mapping[study.storage_mode].upgrade_study(study, version)
