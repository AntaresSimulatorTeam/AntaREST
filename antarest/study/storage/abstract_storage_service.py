# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import tempfile
from abc import ABC
from pathlib import Path
from typing import Optional

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache, study_raw_cache_key
from antarest.core.model import JSON, PublicMode
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.login.model import GroupDTO, Identity
from antarest.login.utils import get_user_impersonator
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Study,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.study_storage import IStudyStorage

logger = logging.getLogger(__name__)


class AbstractStorageService(IStudyStorage, ABC):
    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        cache: ICache,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.cache = cache

    @override
    def get_study_information(
        self,
        study: Study,
        folder_path: Optional[str] = None,
    ) -> StudyMetadataDTO:
        study_workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)

        owner_info = (
            OwnerInfo(id=study.owner.id, name=study.owner.name)
            if study.owner is not None
            else OwnerInfo(name=study.author or "Unknown")
        )

        # replaced mentions of additional data by study."author/editor/horizon"
        return StudyMetadataDTO(
            id=study.id,
            name=study.name,
            version=study.version,
            author=study.author,
            editor=study.editor,
            created=str(study.created_at),
            updated=str(study.updated_at),
            workspace=study_workspace,
            managed=study_workspace == DEFAULT_WORKSPACE_NAME,
            type=study.type,
            archived=study.archived if study.archived is not None else False,
            owner=owner_info,
            groups=[GroupDTO(id=group.id, name=group.name) for group in study.groups],
            public_mode=study.public_mode or PublicMode.NONE,
            horizon=study.horizon,
            folder=folder_path or study.folder,
            tags=[tag.label for tag in study.tags],
            directory_id=study.directory_id,
            parent_id=study.parent_id,
        )

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

    @override
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
            from_cache: Optional[JSON] = None
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

    @override
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

    @override
    def export_study(
        self, metadata: Study, target: Path, outputs: bool = True, archive_format: ArchiveFormat = ArchiveFormat.ZIP
    ) -> Path:
        """
        Export and compress the study inside a 7zip file.

        Args:
            metadata: Study metadata object.
            target: Path of the file to export to.
            outputs: Flag to indicate whether to include the output folder inside the exportation.
            archive_format:

        Returns:
            The 7zip file containing the study files compressed inside.
        """
        path_study = Path(metadata.path)
        with tempfile.TemporaryDirectory(dir=self.config.storage.tmp_dir) as tmpdir:
            logger.info(f"Exporting study {metadata.id} to temporary path {tmpdir}")
            tmp_study_path = Path(tmpdir) / "tmp_copy"
            self.export_study_flat(metadata, tmp_study_path, outputs)
            stopwatch = StopWatch()
            archive_dir(tmp_study_path, target, archive_format=archive_format)
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Study {path_study} exported ({target.suffix} format) in {x}s")
            )
        return target
