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
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import StudyMetadataCreation
from antarest.study.storage.file_study_utils import update_antares_info
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.utils import create_new_empty_study
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@dataclass(frozen=True)
class ResourcePaths:
    study_path: Path
    output_path: Path | None


class FileStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study in the filesystem
    """

    def __init__(
        self,
        command_context: CommandContext,
        study_factory: StudyFactory,
        cache: ICache,
        paths_getter: Callable[[str], ResourcePaths],
    ) -> None:
        self._command_context = command_context
        self._study_factory = study_factory
        self._cache = cache
        self._paths_getter = paths_getter

    @override
    def create_study_dao(self, metadata: StudyMetadataCreation) -> FileStudyTreeDao:
        return self._create_dao(metadata)

    @override
    def get_study_dao(self, study_id: str, is_study_managed: bool) -> FileStudyTreeDao:
        paths = self._paths_getter(study_id)

        file_study = self._study_factory.create_from_fs(paths.study_path, is_study_managed, study_id, paths.output_path)

        return self._build_dao(is_study_managed, file_study)

    def export_study(self, metadata: StudyMetadataCreation, dst_path: Path) -> FileStudyTreeDao:
        return self._create_dao(metadata, dst_path)

    def _create_dao(self, metadata: StudyMetadataCreation, study_path: Path | None = None) -> FileStudyTreeDao:
        study_id = metadata.id
        paths = self._paths_getter(study_id)
        output_path = paths.output_path
        study_path = study_path or paths.study_path

        create_new_empty_study(version=metadata.version, path_study=study_path)

        is_study_managed = metadata.managed

        # We don't want to use the cache as we're creating a new study.
        # In particular, when launching a simulation for a DB study, the cache is filled with the old JOB path so we don't want to use it.
        file_study = self._study_factory.create_from_fs(study_path, is_study_managed, study_id, output_path, False)

        update_antares_info(metadata, file_study.tree, update_author=True)

        return self._build_dao(is_study_managed, file_study)

    def _build_dao(self, is_study_managed: bool, file_study: FileStudy) -> FileStudyTreeDao:
        context = self._command_context
        return FileStudyTreeDao(
            file_study,
            is_study_managed,
            context.generator_matrix_constants,
            context.blob_service,
            context.matrix_service,
            self._cache,
        )
