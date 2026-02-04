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

from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.utils import create_new_empty_study, is_managed, update_antares_info
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class FileStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study in the filesystem
    """

    def __init__(self, command_context: CommandContext, study_factory: StudyFactory) -> None:
        self._command_context = command_context
        self._study_factory = study_factory

    @override
    def create_study_dao(self, study: Study) -> FileStudyTreeDao:
        """The given study object is modified as a side effect"""
        path_study = Path(study.path)

        create_new_empty_study(version=StudyVersion.parse(study.version), path_study=path_study)

        file_study = self._study_factory.create_from_fs(path_study, is_managed(study), study.id)
        update_antares_info(study, file_study.tree, update_author=True)

        study.path = str(path_study)

        context = self._command_context
        dao = FileStudyTreeDao(file_study, context.generator_matrix_constants, context.blob_service)
        return dao
