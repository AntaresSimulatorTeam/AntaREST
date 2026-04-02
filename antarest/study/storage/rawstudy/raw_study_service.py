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
import tempfile
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import StudyDeletionNotAllowed, StudyImportFailed
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.archives import (
    ArchiveFormat,
    archive_dir,
    extract_archive_from_path,
    extract_archive_from_stream,
)
from antarest.core.utils.utils import StopWatch, current_time
from antarest.matrixstore.matrix_uri_mapper import NormalizedMatrixUriMapper, extract_matrix_id
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dtos import StudyDataSynthesis
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, StorageMode, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.utils import (
    fix_study_root,
    is_managed,
    remove_from_cache,
    update_antares_info,
)

logger = logging.getLogger(__name__)


class RawStudyService(AbstractStorageService):
    """
    Manage set of raw studies stored in the workspaces.
    Instantiate and manage tree struct for each request

    """

    def __init__(
        self, config: Config, study_factory: StudyFactory, cache: ICache, matrix_service: ISimpleMatrixService
    ):
        super().__init__(config=config, cache=cache)

        self.study_factory = study_factory
        self._matrix_service = matrix_service
        RawStudyMatrixUsageProvider(StudyMetadataRepository(cache_service=cache), matrix_service=self._matrix_service)

    @property
    def matrix_service(self) -> ISimpleMatrixService:
        return self._matrix_service

    def update_from_raw_meta(
        self, metadata: RawStudy, fallback_on_default: bool | None = False, study_path: Path | None = None
    ) -> None:
        """
        Update metadata from study raw metadata
        Args:
            metadata: study
            fallback_on_default: use default values in case of failure
            study_path: optional study path
        """
        path = study_path or self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(path, is_managed(metadata), study_id="")
        try:
            raw_meta = study.tree.get(["study", "antares"])

            if metadata.editor:
                raw_meta["editor"] = metadata.editor
                study.tree.save(raw_meta, ["study", "antares"])

            metadata.name = raw_meta["caption"]
            metadata.version = str(raw_meta["version"])
            metadata.created_at = datetime.utcfromtimestamp(raw_meta["created"])
            metadata.updated_at = datetime.utcfromtimestamp(raw_meta["lastsave"])

            self._update_study_data_from_files(study, metadata)

        except Exception as e:
            logger.error(
                "Failed to fetch study %s raw metadata!",
                str(metadata.path),
                exc_info=e,
            )
            if fallback_on_default is not None:
                metadata.name = metadata.name or "unnamed"
                metadata.version = metadata.version or "0.0"
                metadata.created_at = metadata.created_at or datetime.now(timezone.utc).replace(tzinfo=None)
                metadata.updated_at = metadata.updated_at or datetime.now(timezone.utc).replace(tzinfo=None)

                metadata.author = metadata.author or "Unknown"
                metadata.editor = metadata.editor or "Unknown"

            else:
                raise e

    def update_name_and_version_from_raw_meta(self, metadata: RawStudy) -> bool:
        """
        Update name from study raw metadata
        Args:
            metadata: study
        Returns: a boolean indicating if the name or version has changed
        """
        path = self.get_study_path(metadata)
        try:
            study = self.study_factory.create_from_fs(path, is_managed(metadata), study_id="")
            raw_meta = study.tree.get(["study", "antares"])
            version_as_string = str(raw_meta["version"])
            if metadata.name != raw_meta["caption"] or metadata.version != version_as_string:
                logger.info(
                    f"Updating name/version for study {metadata.id} ({metadata.name}) to {raw_meta['caption']}/{version_as_string}"
                )
                metadata.name = raw_meta["caption"]
                metadata.version = version_as_string
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to update study %s name and version from raw metadata!",
                str(metadata.path),
                exc_info=e,
            )
            return False

    @override
    def exists(self, study: Study) -> bool:
        """
        Check if the study exists in the filesystem.

        Args:
            study: The study to check.

        Returns: true if study presents in disk, false else.
        """
        if study.archived:
            archive_path = self.find_archive_path(study)
            return archive_path.is_file()

        path = self.get_study_path(study)
        return path.joinpath("study.antares").is_file()

    @override
    def get_raw(
        self,
        metadata: Study,
        use_cache: bool = True,
        output_dir: Path | None = None,
    ) -> FileStudy:
        """
        Fetch a study object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object

        """
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        return self.study_factory.create_from_fs(
            study_path, is_managed(metadata), metadata.id, output_dir, use_cache=use_cache
        )

    @override
    def get_synthesis(self, metadata: Study) -> StudyDataSynthesis:
        self._check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        study = self.study_factory.create_from_fs(study_path, is_managed(metadata), metadata.id)
        return StudyDataSynthesis.from_study_config(study.config)

    @override
    def copy(
        self,
        src_meta: Study,
        dest_study_name: str,
        groups: Sequence[str],
        destination_folder: PurePosixPath,
    ) -> RawStudy:
        """
        Create a new RAW study by copying a reference study.

        Args:
            src_meta: The source study that you want to copy.
            dest_study_name: The name for the destination study.
            groups: A list of groups to assign to the destination study.
            destination_folder: The path for the destination study. If not provided, the destination study will be created in the same directory as the source study.

        Returns:
            The newly created study.
        """
        self._check_study_exists(src_meta)

        dest_study = self.build_raw_study(dest_study_name, groups, src_meta, destination_folder)

        src_path = self.get_study_path(src_meta)
        dest_path = self.get_study_path(dest_study)

        shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns("output"))

        study = self.study_factory.create_from_fs(dest_path, is_managed(src_meta), study_id=dest_study.id)

        update_antares_info(dest_study, study.tree, update_author=False)

        return dest_study

    def build_raw_study(
        self, dest_study_name: str, groups: Sequence[str], src_study: Study, destination_folder: PurePosixPath
    ) -> RawStudy:
        dest_id = str(uuid4())
        now_utc = current_time()
        dest_study = RawStudy(
            id=dest_id,
            name=dest_study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(self.config.get_workspace_path() / dest_id),
            created_at=now_utc,
            updated_at=now_utc,
            version=src_study.version,
            author=src_study.author,
            editor=self._get_current_user_name(),
            horizon=src_study.horizon,
            public_mode=PublicMode.NONE if groups else PublicMode.READ,
            groups=groups,
            folder=str(destination_folder / dest_id),
        )
        return dest_study

    @override
    def delete(self, metadata: Study) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        self._check_study_exists(metadata)
        if self.config.storage.allow_deletion or is_managed(metadata):
            study_path = self.get_study_path(metadata)
            shutil.rmtree(study_path, ignore_errors=True)
            remove_from_cache(self.cache, metadata.id)
        else:
            raise StudyDeletionNotAllowed(metadata.id)

    def _extract_and_setup(self, study: RawStudy, study_path: Path, source: Path | BinaryIO) -> None:
        study_path.mkdir()
        try:
            if isinstance(source, Path):
                extract_archive_from_path(source, study_path)
            else:
                extract_archive_from_stream(source, study_path, tmp_dir=self.config.storage.tmp_dir)
            fix_study_root(study_path)
            self.update_from_raw_meta(study, study_path=study_path)
        except Exception:
            shutil.rmtree(study_path)
            raise
        try:
            self.checks_antares_web_compatibility(study)
        except NotImplementedError as e:
            raise StudyImportFailed(study.name or "Unknown Study", e.args[0])
        study.path = str(study_path)

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

    @override
    def export_study_flat(
        self,
        metadata: Study,
        dst_path: Path,
        denormalize: bool = True,
    ) -> None:
        try:
            if metadata.archived:
                if isinstance(metadata, RawStudy):
                    self.unarchive(metadata)  # may raise BadArchiveContent
                else:
                    raise TypeError(f"unarchive requires a RawStudy, got {type(metadata)}")

            self.export_study_to_flat_directory(
                Path(metadata.path),
                dst_path,
                denormalize,
                is_study_managed=is_managed(metadata),
            )

        finally:
            if metadata.archived:
                shutil.rmtree(metadata.path, ignore_errors=True)

    def archive(self, study: RawStudy) -> None:
        archive_path = self.config.storage.archive_dir.joinpath(f"{study.id}{ArchiveFormat.SEVEN_ZIP}")

        path_study = Path(study.path)
        with tempfile.TemporaryDirectory(dir=self.config.storage.tmp_dir) as tmpdir:
            logger.info(f"Exporting study {study.id} to temporary path {tmpdir}")
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(study, tmp_study_path)
            stopwatch = StopWatch()
            archive_dir(tmp_study_path, archive_path, archive_format=ArchiveFormat.SEVEN_ZIP)
            logger.info(f"Study {path_study} exported ({archive_path.suffix} format) in {stopwatch}s")

        shutil.rmtree(study.path)
        remove_from_cache(cache=self.cache, root_id=study.id)
        self.cache.invalidate(study.id)

    # noinspection SpellCheckingInspection
    def unarchive(self, study: RawStudy) -> None:
        """
        Extract the archive of a study directly from its archive path,
        bypassing stream-based extraction for better performance.

        Args:
            study: The study to be unarchived.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        archive_path = self.find_archive_path(study)
        study_path = Path(study.path).resolve()
        workspace_path = self.config.get_workspace_path(workspace=study.workspace).resolve()
        if not study_path.is_relative_to(workspace_path):
            raise ValueError(f"Study path '{study_path}' is not within workspace '{workspace_path}'")
        self._extract_and_setup(study, study_path, archive_path)

    def find_archive_path(self, study: Study) -> Path:
        """
        Fetch for archive path of a study if it exists else raise an incorrectly archived study.

        Args:
            study: The study to get the archive path for.

        Returns:
            The full path of the archive file (zip or 7z).
        """
        archive_dir: Path = self.config.storage.archive_dir
        for suffix in list(ArchiveFormat):
            path = archive_dir.joinpath(f"{study.id}{suffix}")
            if path.is_file():
                return path
        raise FileNotFoundError(f"Study {study.id} archiving process is corrupted (no archive file found).")

    @override
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        if metadata.archived:
            return self.find_archive_path(metadata)
        return Path(metadata.path)

    def check_and_update_study_version_in_database(self, study: RawStudy) -> None:
        try:
            study_path = self.get_study_path(study)
            if study_path:
                config = FileStudyTreeConfig(
                    study_path=study_path,
                    path=study_path,
                    study_id="",
                    version=StudyVersion.parse(0),
                )
                raw_study = self.study_factory.create_from_config(config, NormalizedMatrixUriMapper.NORMALIZED)
                file_metadata = raw_study.get(url=["study", "antares"])
                study_version = str(file_metadata.get("version", study.version))
                if study_version != study.version:
                    logger.warning(
                        f"Study version in file ({study_version}) is different from the one stored in db ({study.version}), returning file version"
                    )
                    study.version = study_version
        except Exception as e:
            logger.error(
                "Failed to check and/or update study version in database for study %s",
                study.id,
                exc_info=e,
            )

    @staticmethod
    def checks_antares_web_compatibility(study: Study) -> None:
        """
        A new compatibility section has been introduced with the Simulator version 9.2
        """
        pass

    def normalize_study(self, study: Study) -> None:
        """
        Method used to normalize a study.
        It will put every matrix in the study in the matrix-store.
        """
        if study.storage_mode == StorageMode.DATABASE:
            # Nothing to do
            return

        file_study = self.get_raw(study)
        matrix_nodes = file_study.tree.get_matrix_nodes_to_normalize()
        if not matrix_nodes:
            return

        matrix_ids = self._matrix_service.create_batch(node.parse_content() for node in matrix_nodes)
        for k, node in enumerate(matrix_nodes):
            node.matrix_mapper.save_matrix(node, matrix_ids[k])

    def denormalize_study(self, study: Study | FileStudy) -> None:
        """
        Method used to denormalize a study.
        It will replace every `.link` file in the study with its content stored in the matrix-store.
        """
        if not isinstance(study, FileStudy):
            if study.storage_mode == StorageMode.DATABASE:
                # Nothing to do
                return
            else:
                study = self.get_raw(study)

        matrix_nodes = study.tree.get_matrix_nodes_to_denormalize()
        if not matrix_nodes:
            return

        matrices_mapping: dict[str, list[MatrixNode]] = {}
        for node in matrix_nodes:
            link_content = node.matrix_mapper.get_link_content(node)
            assert link_content is not None
            matrices_mapping.setdefault(extract_matrix_id(link_content), []).append(node)

        for matrix_content in self._matrix_service.yield_matrices(list(matrices_mapping.keys())):
            for node in matrices_mapping[matrix_content.id]:
                node.write_dataframe(matrix_content.data)

    def export_study_to_flat_directory(
        self,
        study_dir: Path,
        dest: Path,
        denormalize: bool = True,
        is_study_managed: bool = True,
    ) -> None:
        start_time = time.time()

        def ignore_outputs(directory: str, _: Sequence[str]) -> Sequence[str]:
            return ["output"] if str(directory) == str(study_dir) else []

        shutil.copytree(src=study_dir, dst=dest, ignore=ignore_outputs)

        stop_time = time.time()
        duration = f"{stop_time - start_time:.3f}"
        logger.info(f"Study '{study_dir}' exported (flat mode) in {duration}s")
        if denormalize:
            study = self.study_factory.create_from_fs(dest, is_study_managed, "", use_cache=False)
            self.denormalize_study(study)
            duration = f"{time.time() - stop_time:.3f}"
            logger.info(f"Study '{study_dir}' denormalized in {duration}s")
