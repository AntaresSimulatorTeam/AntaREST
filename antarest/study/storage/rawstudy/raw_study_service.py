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
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.abstract.abstract_storage_service import AbstractStorageService
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
