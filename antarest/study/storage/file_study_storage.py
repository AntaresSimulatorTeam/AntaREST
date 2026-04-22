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
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.utils import current_time
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import get_current_user_name, is_managed, update_antares_info
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, cache: ICache, config: Config, command_context: CommandContext, study_factory: StudyFactory):
        self._command_context = command_context
        self._cache = cache
        self._config = config
        self._study_factory = study_factory
        self._matrix_service = command_context.matrix_service

    @override
    def get_dao(self, study: Study) -> FileStudyTreeDao:
        factory = FileStudyDaoFactory(self._command_context, self._study_factory, self._cache)
        return factory.get_study_dao(study)

    @override
    def copy(self, src_study: Study, dst_name: str, groups: list[str], destination_folder: PurePosixPath) -> Study:
        dest_study = self._build_raw_study(dst_name, groups, src_study, destination_folder)

        src_path = Path(src_study.path)
        dest_path = Path(dest_study.path)

        shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns("output"))

        file_study = self._get_file_study(dest_path, is_managed(src_study), dest_study.id)

        update_antares_info(dest_study, file_study.tree, update_author=False)

        return dest_study

    @override
    def write_study_to_filesytem(self, study: Study) -> Path:
        study_path = Path(study.path)
        file_study = self._get_file_study(study_path, is_managed(study), study.id)
        self._denormalize_file_study(file_study)
        return study_path

    @override
    def normalize_study(self, study: Study) -> None:
        file_study = self._get_file_study(Path(study.path), is_managed(study), study.id)
        matrix_nodes = file_study.tree.get_matrix_nodes_to_normalize()
        if not matrix_nodes:
            return

        matrix_ids = self._matrix_service.create_batch(node.parse_content() for node in matrix_nodes)
        for k, node in enumerate(matrix_nodes):
            node.matrix_mapper.save_matrix(node, matrix_ids[k])

    @override
    def import_study(self, study: RawStudy, stream: BinaryIO) -> RawStudy:
        self.normalize_study(study)
        return study

    def update_from_raw_metadata(self, study: Study) -> None:
        """
        The given `study` object needs to be updated according to the real filesystem data
        """
        file_study = self._get_file_study(Path(study.path), is_managed(study))
        try:
            raw_meta = file_study.tree.get(["study", "antares"])

            if study.editor:
                raw_meta["editor"] = study.editor
                file_study.tree.save(raw_meta, ["study", "antares"])

            study.name = raw_meta["caption"]
            study.version = str(raw_meta["version"])
            study.created_at = datetime.utcfromtimestamp(raw_meta["created"])
            study.updated_at = datetime.utcfromtimestamp(raw_meta["lastsave"])

            self._update_study_data_from_files(file_study, study)

        except Exception as e:
            logger.error("Failed to fetch study %s raw study!", str(study.path), exc_info=e)
            study.name = study.name or "unnamed"
            study.created_at = study.created_at or current_time()
            study.updated_at = study.updated_at or current_time()
            study.author = study.author or "Unknown"
            study.editor = study.editor or "Unknown"

    def update_name_and_version_from_raw_meta(self, study: RawStudy) -> bool:
        path = Path(study.path)
        try:
            file_study = self._get_file_study(path, is_managed(study))
            raw_meta = file_study.tree.get(["study", "antares"])
            version_as_string = str(raw_meta["version"])
            if study.name != raw_meta["caption"] or study.version != version_as_string:
                logger.info(
                    f"Updating name/version for study {study.id} ({study.name}) to {raw_meta['caption']}/{version_as_string}"
                )
                study.name = raw_meta["caption"]
                study.version = version_as_string
                return True
            return False
        except Exception as e:
            logger.error("Failed to update study %s name and version from raw metadata!", str(study.path), exc_info=e)
            return False

    def _update_study_data_from_files(self, file_study: FileStudy, study: Study) -> None:
        logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        study_antares = file_study.tree.get(url=["study", "antares"])
        author = study_antares.get("author")
        editor = study_antares.get("editor", author)
        assert isinstance(author, str)
        assert isinstance(editor, str)
        assert isinstance(horizon, (str, int))
        study.horizon = horizon
        study.author = author
        study.editor = editor

    def _get_file_study(self, study_path: Path, managed: bool, study_id: str = "") -> FileStudy:
        return self._study_factory.create_from_fs(study_path, managed, study_id=study_id)

    def _denormalize_file_study(self, file_study: FileStudy) -> None:
        matrix_nodes = file_study.tree.get_matrix_nodes_to_denormalize()
        if not matrix_nodes:
            return

        matrices_mapping: dict[str, list[MatrixNode]] = {}
        for node in matrix_nodes:
            link_content = node.matrix_mapper.get_link_content(node)
            assert link_content is not None
            matrices_mapping.setdefault(extract_matrix_id(link_content), []).append(node)

        for matrix_content in self._matrix_service.yield_matrices(list(matrices_mapping)):
            for node in matrices_mapping[matrix_content.id]:
                node.write_dataframe(matrix_content.data)

    def _build_raw_study(
        self, dest_study_name: str, groups: list[str], src_study: Study, destination_folder: PurePosixPath
    ) -> RawStudy:
        dest_id = str(uuid4())
        now_utc = current_time()
        dest_study = RawStudy(
            id=dest_id,
            name=dest_study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(self._config.get_workspace_path() / dest_id),
            created_at=now_utc,
            updated_at=now_utc,
            version=src_study.version,
            author=src_study.author,
            editor=get_current_user_name(),
            horizon=src_study.horizon,
            public_mode=PublicMode.NONE if groups else PublicMode.READ,
            groups=groups,
            folder=str(destination_folder / dest_id),
        )
        return dest_study
