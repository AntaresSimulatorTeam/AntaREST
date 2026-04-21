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

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.study_storage_interface import IStudyStorage

logger = logging.getLogger(__name__)


class FileStudyStorage(IStudyStorage):
    def __init__(self, cache: ICache, config: Config, matrix_service: ISimpleMatrixService):
        self._matrix_service = matrix_service
        self.cache = cache
        self.config = config
