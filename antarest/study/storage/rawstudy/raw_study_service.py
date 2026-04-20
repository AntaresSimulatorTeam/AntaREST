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
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.utils.utils import current_time
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider

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

    @override
    def exists(self, study: Study) -> bool:
        raise NotImplementedError()

    @override
    def copy(
        self,
        src_meta: Study,
        dest_study_name: str,
        groups: Sequence[str],
        destination_folder: PurePosixPath,
    ) -> RawStudy:
        raise NotImplementedError()

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
        raise NotImplementedError()

    def import_study(self, metadata: RawStudy, stream: BinaryIO) -> RawStudy:
        raise NotImplementedError()

    @override
    def export_study_flat(self, metadata: Study, dst_path: Path, denormalize: bool = True) -> None:
        raise NotImplementedError()

    def archive(self, study: RawStudy) -> None:
        raise NotImplementedError()

    # noinspection SpellCheckingInspection
    def unarchive(self, study: RawStudy) -> None:
        raise NotImplementedError()

    def find_archive_path(self, study: Study) -> Path:
        raise NotImplementedError()
