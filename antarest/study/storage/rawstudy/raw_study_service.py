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
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from antares.study.version import StudyVersion
from markupsafe import escape
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import StudyNotFoundError
from antarest.core.interfaces.cache import ICache
from antarest.core.utils.archives import (
    ArchiveFormat,
    archive_dir,
    extract_archive_from_path,
    extract_archive_from_stream,
)
from antarest.core.utils.utils import StopWatch
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory, ResourcePaths
from antarest.study.model import RawStudy, StorageMode, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract.abstract_study_service import AbstractStudyService
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.file_study_storage import FileStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import (
    StudyMetadataCreation,
    build_raw_study_from_source,
    fix_study_root,
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
        ctx = command_context
        self._study_dao_factories: dict[StorageMode, StudyFactoryDao] = {
            StorageMode.DATABASE: DatabaseStudyDaoFactory(ctx.matrix_service, ctx.generator_matrix_constants),
            StorageMode.FILESYSTEM: FileStudyDaoFactory(command_context, study_factory, cache, self.get_study_paths),
        }
        self._file_study_storage = FileStudyStorage(self._matrix_service, study_factory)
        self._database_study_storage = DatabaseStudyStorage(self._matrix_service, self._study_dao_factories)
        self._storage_mapping: dict[StorageMode, IStudyStorage] = {
            StorageMode.FILESYSTEM: self._file_study_storage,
            StorageMode.DATABASE: self._database_study_storage,
        }
        RawStudyMatrixUsageProvider(repository, self._matrix_service, self._storage_mapping)
        self.cache = cache

    @override
    def copy(self, src_study: Study, dest_name: str, groups: list[str], destination_folder: PurePosixPath) -> RawStudy:
        new_study = build_raw_study_from_source(
            dest_name, self._config.get_workspace_path(), groups, src_study, destination_folder
        )
        return self._storage_mapping[src_study.storage_mode].copy(src_study, new_study)

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

        archive_path = self._config.storage.archive_dir.joinpath(f"{study.id}{ArchiveFormat.SEVEN_ZIP}")

        try:
            stopwatch = StopWatch()
            archive_dir(dst_path, archive_path, False, ArchiveFormat.SEVEN_ZIP)
            logger.info(f"Study {study.id} exported ({archive_path.suffix} format) in {stopwatch}s")
        except Exception as e:
            logger.warning(f"Failed to archive study {study.id}", exc_info=e)
            archive_path.unlink(missing_ok=True)

        else:
            # Remove the source study folder if everything went well
            shutil.rmtree(Path(study.path))
            remove_from_cache(cache=self.cache, root_id=study.id)
            self.cache.invalidate(study.id)

        finally:
            # Remove the temporary folder
            shutil.rmtree(dst_path, ignore_errors=True)

    def unarchive(self, study: RawStudy) -> None:
        archive_path = self.find_archive_path(study)
        self._extract_and_setup(study, archive_path)
        archive_path.unlink()

    def normalize_study(self, study: Study) -> None:
        self._storage_mapping[study.storage_mode].normalize_study(study)

    def update_from_raw_metadata(self, study: RawStudy) -> None:
        self._file_study_storage.update_from_raw_metadata(study)

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        return self._file_study_storage.update_name_and_version_from_raw_meta(study)

    def import_study(self, study: RawStudy, stream: BinaryIO) -> RawStudy:
        """
        Import study in the directory of the study.

        Args:
            study: study information.
            stream: binary content of the study compressed in ZIP or 7z format.

        Returns:
            Updated study information.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        self._extract_and_setup(study, stream)
        self._storage_mapping[study.storage_mode].import_study(Path(study.path), study.id)
        return study

    def _extract_and_setup(self, study: RawStudy, source: Path | BinaryIO) -> None:
        """
        The source is extracted to the filesystem inside the study `path` attribute.
        """
        study_path = Path(study.path)
        try:
            if isinstance(source, Path):
                extract_archive_from_path(source, study_path)
            else:
                extract_archive_from_stream(source, study_path, tmp_dir=self._config.storage.tmp_dir)
            fix_study_root(study_path)
            self.update_from_raw_metadata(study)
        except Exception:
            shutil.rmtree(study_path, ignore_errors=True)
            raise

    def denormalize_study(self, study: Study) -> None:
        self._file_study_storage.denormalize_study(study)
