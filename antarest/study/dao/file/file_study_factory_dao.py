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
from pathlib import Path

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.utils import create_new_empty_study, is_managed, update_antares_info
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


class FileStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study in the filesystem
    """

    def __init__(self, command_context: CommandContext, study_factory: StudyFactory, cache: ICache) -> None:
        self._command_context = command_context
        self._study_factory = study_factory
        self._cache = cache

    @override
    def create_study_dao(self, study: Study, denormalize_matrices: bool = False) -> FileStudyTreeDao:
        study_path = Path(study.path)
        if isinstance(study, VariantStudy):
            study_path = study.snapshot_dir

        # If the study already exists, we won't override it but instead use the existing one to build the DAO object.
        # This case happens in particular with variant studies snapshots.
        if not study_path.exists():
            create_new_empty_study(version=StudyVersion.parse(study.version), path_study=study_path)

        file_study = self._study_factory.create_from_fs(study_path, not denormalize_matrices, study.id)
        update_antares_info(study, file_study.tree, update_author=True)

        context = self._command_context
        return FileStudyTreeDao(
            file_study,
            is_managed(study),
            context.generator_matrix_constants,
            context.blob_service,
            context.matrix_service,
            self._cache,
        )
