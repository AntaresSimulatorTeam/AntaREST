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
from abc import ABC
from pathlib import Path

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.archives import ArchiveFormat
from antarest.login.model import GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Study,
    StudyMetadataDTO,
)
from antarest.study.storage.study_service_interface import IStudyService
from antarest.study.storage.utils import get_disk_usage, remove_from_cache

logger = logging.getLogger(__name__)


class AbstractService(IStudyService, ABC):
    def __init__(self, cache: ICache, config: Config):
        self._cache = cache
        self._config = config

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

    @override
    def delete_from_filesystem(self, study: Study) -> None:
        study_path = self._get_study_path_on_file_system(study)
        shutil.rmtree(study_path, ignore_errors=True)
        remove_from_cache(self._cache, study.id)

    def _get_study_path_on_file_system(self, metadata: Study) -> Path:
        if metadata.archived:
            return self.find_archive_path(metadata)
        return Path(metadata.path)

    def find_archive_path(self, study: Study) -> Path:
        """
        Fetch for archive path of a study if it exists else raise an incorrectly archived study.

        Args:
            study: The study to get the archive path for.

        Returns:
            The full path of the archive file (zip or 7z).
        """
        archive_dir: Path = self._config.storage.archive_dir
        for suffix in list(ArchiveFormat):
            path = archive_dir.joinpath(f"{study.id}{suffix}")
            if path.is_file():
                return path
        raise FileNotFoundError(f"Study {study.id} archiving process is corrupted (no archive file found).")

    @override
    def get_disk_usage(self, study: Study) -> int:
        study_path = self._get_study_path_on_file_system(study)
        return get_disk_usage(study_path)
