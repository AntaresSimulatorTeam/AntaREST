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
from abc import ABC

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import GroupDTO, Identity
from antarest.login.utils import get_user_impersonator
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Study,
    StudyMetadataDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_storage import IStudyStorage

logger = logging.getLogger(__name__)


class AbstractStorageService(IStudyStorage, ABC):
    def __init__(self, config: Config, cache: ICache):
        self.config: Config = config
        self.cache = cache

    @override
    def get_study_information(
        self,
        study: Study,
        folder_path: str | None = None,
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
