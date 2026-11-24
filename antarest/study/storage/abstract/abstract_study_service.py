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
import uuid
from abc import ABC
from pathlib import Path
from typing import NamedTuple

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.archives import ArchiveFormat, is_archive_format
from antarest.login.model import GroupDTO
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    OwnerInfo,
    Study,
    StudyMetadataDTO,
)
from antarest.study.storage.file_study_utils import check_study_path
from antarest.study.storage.study_service_interface import IStudyService
from antarest.study.storage.utils import remove_from_cache

logger = logging.getLogger(__name__)


class StudyArchive(NamedTuple):
    study_id: str
    path: Path


class StudyArchivesScan(NamedTuple):
    archives: list[StudyArchive]
    unexpected_entries: list[Path]


def _parse_study_id_from_archive(entry: Path) -> str | None:
    """Return the study ID of a study archive, or None if `entry` is not one."""
    if not entry.is_file() or not is_archive_format(entry.suffix):
        return None
    try:
        study_id = str(uuid.UUID(entry.stem))
    except ValueError:
        return None
    # Reject non-canonical UUIDs (upper-case, no hyphens...): they are not study IDs.
    return study_id if study_id == entry.stem else None


class AbstractStudyService(IStudyService, ABC):
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
            storage_mode=study.storage_mode,
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
        if study.archived:
            # The study is already deleted from the database: a missing archive must not abort the cleanup.
            try:
                self.find_archive_path(study).unlink()
            except FileNotFoundError as e:
                logger.warning(f"No archive to delete for study {study.id}: {e}")
        # Database-mode studies have no file-system footprint: nothing to remove.
        elif study.path is not None:
            shutil.rmtree(check_study_path(study), ignore_errors=True)

        remove_from_cache(self._cache, study.id)

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

    def list_study_archives(self) -> StudyArchivesScan:
        """List the study archives and the other entries of the archive directory."""
        archive_dir: Path = self._config.storage.archive_dir
        if not archive_dir.is_dir():
            return StudyArchivesScan(archives=[], unexpected_entries=[])
        archives: list[StudyArchive] = []
        unexpected_entries: list[Path] = []
        for entry in sorted(archive_dir.iterdir()):
            study_id = _parse_study_id_from_archive(entry)
            if study_id is None:
                unexpected_entries.append(entry)
            else:
                archives.append(StudyArchive(study_id=study_id, path=entry))
        return StudyArchivesScan(archives=archives, unexpected_entries=unexpected_entries)
