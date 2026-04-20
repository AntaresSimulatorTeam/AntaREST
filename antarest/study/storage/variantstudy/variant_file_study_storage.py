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
from pathlib import Path

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyNotFoundError,
)
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.model import JSON, StudyPermissionType
from antarest.core.tasks.service import ITaskService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import (
    StorageMode,
    Study,
)
from antarest.study.storage.abstract.abstract_file_study_storage import AbstractFileStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.inode import OriginalFile
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import (
    assert_permission,
    is_managed,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository

logger = logging.getLogger(__name__)


def _cast_study_to_variant(study: Study) -> VariantStudy:
    if not isinstance(study, VariantStudy):
        raise TypeError(f"The type of the study must be {VariantStudy}, not {type(study)}")
    return study


class VariantFileStudyStorage(AbstractFileStudyStorage):
    def __init__(
        self,
        task_service: ITaskService,
        cache: ICache,
        raw_study_service: RawStudyService,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        repository: VariantStudyRepository,
        event_bus: IEventBus,
        config: Config,
        matrix_service: ISimpleMatrixService,
    ):
        super().__init__(config=config, cache=cache)
        self.task_service = task_service
        self.raw_study_service = raw_study_service
        self.repository = repository
        self.event_bus = event_bus
        self.command_factory = command_factory
        self.study_factory = study_factory
        self._matrix_service = matrix_service

    def _update_editor(self, study: VariantStudy) -> None:
        user_name = self._get_current_user_name()
        study.editor = user_name
        self.repository.save(study)

    def _get_variant_study(
        self,
        study_id: str,
    ) -> VariantStudy:
        """
        Get variant study, and check READ permissions.

        Args:
            study_id: The study identifier.

        Returns:
            The variant study.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
        """
        study = self._get_study_by_id(study_id)

        assert isinstance(study, VariantStudy)
        return study

    def _get_study_by_id(
        self,
        study_id: str,
    ) -> Study:
        """
        Get study, and check READ permissions.

        Args:
            study_id: The study identifier.

        Returns:
            The variant study.

        Raises:
            StudyNotFoundError: If the study does not exist (HTTP status 404).
            MustBeAuthenticatedError: If the user is not authenticated (HTTP status 403).
        """
        study = self.repository.get(study_id)

        if study is None:
            raise StudyNotFoundError(study_id)

        assert_permission(study, StudyPermissionType.READ)
        return study

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
            use_cache: indicate if cache should be used

        Returns: study data formatted in json
        """
        if isinstance(metadata, VariantStudy):
            self._safe_generation(metadata, timeout=600)
        else:
            raise TypeError(f"Expected {VariantStudy} but received {type(metadata)}")
        self.repository.refresh(metadata)
        return super().get(
            metadata=metadata,
            url=url,
            depth=depth,
            formatted=formatted,
            use_cache=use_cache,
        )

    @override
    def get_file(
        self,
        metadata: Study,
        url: str = "",
        use_cache: bool = True,
    ) -> OriginalFile:
        """
        Entry point to fetch for a file inside a study folder.
        Args:
            metadata: study
            url: path data inside study to reach
            use_cache: indicate if cache should be used to fetch study tree

        Returns: the file content and extension
        """
        if isinstance(metadata, VariantStudy):
            self._safe_generation(metadata, timeout=600)
        else:
            raise TypeError(f"Expected {VariantStudy} but received {type(metadata)}")
        self.repository.refresh(metadata)
        return super().get_file(
            metadata=metadata,
            url=url,
            use_cache=use_cache,
        )

    @override
    def get_raw(
        self,
        metadata: Study,
        use_cache: bool = True,
        output_dir: Path | None = None,
    ) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study
            use_cache: use cache
            output_dir: optional output dir override
        Returns: the config and study tree object
        """
        variant = _cast_study_to_variant(metadata)
        self._safe_generation(variant)

        study_path = self.get_study_path(variant)
        return self.study_factory.create_from_fs(
            study_path,
            is_managed(variant),
            variant.id,
            output_dir or Path(variant.path) / "output",
            use_cache=use_cache,
        )

    @override
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        variant = _cast_study_to_variant(metadata)
        return variant.snapshot_dir

    @override
    def normalize_study(self, study: Study) -> None:
        if study.storage_mode == StorageMode.DATABASE:
            # Nothing to do
            return

        file_study = self.get_raw(study)
        self.raw_study_service.normalize_file_study(file_study)

    @override
    def exists(self, metadata: Study) -> bool:
        """
        Check if the study snapshot exists and is up-to-date.

        Args:
            metadata: Study metadata.

        Returns: `True` if the study is present on disk, `False` otherwise.
        """
        if not isinstance(metadata, VariantStudy):
            return False

        return (
            (metadata.snapshot is not None)
            and (metadata.snapshot.created_at >= metadata.updated_at)
            and (self.get_study_path(metadata) / "study.antares").is_file()
        )
