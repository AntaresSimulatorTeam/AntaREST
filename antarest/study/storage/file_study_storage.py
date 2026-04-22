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

        src_path = self.get_study_path(src_study)
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

    def _get_file_study(self, study_path: Path, managed: bool, study_id: str) -> FileStudy:
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
