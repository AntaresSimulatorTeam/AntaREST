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

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache, study_raw_cache_key
from antarest.core.model import JSON
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Identity
from antarest.login.utils import get_user_impersonator
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
from antarest.study.storage.study_storage_interface import IStudyStorage

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, cache: ICache, config: Config, matrix_service: ISimpleMatrixService):
        super().__init__(config=config, cache=cache, matrix_service=matrix_service)
        self._matrix_service = matrix_service
        self.cache = cache
        self.config = config

    def denormalize_study(self, study: Study) -> None:
        file_study = self.get_raw(study)
        self.denormalize_file_study(file_study)

    def denormalize_file_study(self, file_study: FileStudy) -> None:
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

    def _update_study_data_from_files(self, file_study: FileStudy, metadata: Study) -> None:
        logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        study_antares = file_study.tree.get(url=["study", "antares"])
        author = study_antares.get("author")
        editor = study_antares.get("editor", author)
        assert isinstance(author, str)
        assert isinstance(editor, str)
        assert isinstance(horizon, (str, int))
        metadata.horizon = horizon
        metadata.author = author
        metadata.editor = editor

    def get(
        self,
        metadata: Study,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
        use_cache: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted
            use_cache: indicate if the cache must be used

        Returns: study data formatted in json

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata, use_cache)
        parts = [item for item in url.split("/") if item]

        if url == "" and depth == -1:
            cache_id = study_raw_cache_key(metadata.id)
            from_cache: JSON | None = None
            if use_cache:
                from_cache = self.cache.get(cache_id)
            if from_cache is not None:
                logger.info(f"Raw Study {metadata.id} read from cache")
                data = from_cache
            else:
                data = study.tree.get(parts, depth=depth, formatted=formatted)
                self.cache.put(cache_id, data)
                logger.info(f"Cache new entry from RawStudyService (studyID: {metadata.id})")
        else:
            data = study.tree.get(parts, depth=depth, formatted=formatted)
        del study
        return data

    def get_file(
        self,
        metadata: Study,
        url: str = "",
        use_cache: bool = True,
    ) -> OriginalFile:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            use_cache: indicate if the cache must be used

        Returns: a file content with its extension and name

        """
        self._check_study_exists(metadata)
        study = self.get_raw(metadata, use_cache)
        parts = [item for item in url.split("/") if item]

        file_node = study.tree.get_node(parts)

        return file_node.get_file_content()

    @staticmethod
    def _get_user_name_from_id(user_id: int) -> str:
        """
        Utility method that retrieves a user's name based on their id.
        Args:
            user_id: user id (user must exist)
        Returns: String representing the user's name
        """
        user_obj: Identity | None = db.session.get(Identity, user_id)
        if user_obj is None:
            return "Unnamed"
        return str(user_obj.name)

    def _get_current_user_name(self) -> str:
        return self._get_user_name_from_id(get_user_impersonator())
