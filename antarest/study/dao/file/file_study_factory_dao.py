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
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.utils import create_new_empty_study, is_managed, update_antares_info
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class FileStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study in the filesystem
    """

    def __init__(self, command_context: CommandContext, study_factory: StudyFactory, cache: ICache) -> None:
        self._command_context = command_context
        self._study_factory = study_factory
        self._cache = cache

    @override
    def create_study_dao(self, study: Study) -> FileStudyTreeDao:
        return self._build_dao(study, create_study=True)

    @override
    def get_study_dao(self, study: Study) -> FileStudyTreeDao:
        return self._build_dao(study, create_study=False)

    def _build_dao(self, study: Study, create_study: bool) -> FileStudyTreeDao:
        # We need to differentiate `RawStudy` and `VariantStudy` to be able to parse the config
        if isinstance(study, RawStudy):
            output_path = None
        else:
            output_path = Path(study.path) / "output"

        study_path = study.get_path()
        if create_study:
            create_new_empty_study(version=StudyVersion.parse(study.version), path_study=study_path)

        is_study_managed = is_managed(study)
        file_study = self._study_factory.create_from_fs(study_path, is_study_managed, study.id, output_path)

        if create_study:
            # We do not want to update the `study.antares` file each time we're building the DAO object
            update_antares_info(study, file_study.tree, update_author=True)

        context = self._command_context
        return FileStudyTreeDao(
            file_study,
            is_study_managed,
            context.generator_matrix_constants,
            context.blob_service,
            context.matrix_service,
            self._cache,
        )
