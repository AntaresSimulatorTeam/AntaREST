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

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, cache: ICache, config: Config, command_context: CommandContext):
        self._command_context = command_context
        self._cache = cache
        self.config = config

    @override
    def get_dao(self, study: Study) -> FileStudyTreeDao:
        is_study_managed = is_managed(study)
        return FileStudyTreeDao(
            self.get_file_study(study),
            is_study_managed,
            self._command_context.generator_matrix_constants,
            self._command_context.blob_service,
            self._command_context.matrix_service,
            self._cache,
        )

    def get_file_study(self, study: Study) -> FileStudy:
        raise NotImplementedError()
