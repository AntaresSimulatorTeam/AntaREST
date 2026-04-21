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

from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, cache: ICache, command_context: CommandContext, study_factory: StudyFactory):
        self._command_context = command_context
        self._cache = cache
        self._study_factory = study_factory

    @override
    def get_dao(self, study: Study) -> FileStudyTreeDao:
        factory = FileStudyDaoFactory(self._command_context, self._study_factory, self._cache)
        return factory.get_study_dao(study)
