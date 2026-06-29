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
from typing import Iterable

from typing_extensions import override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import StorageMode
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository
from antarest.study.storage.study_storage_interface import IStudyStorage

logger = logging.getLogger(__name__)


class RawStudyMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(
        self,
        study_metadata_repo: StudyMetadataRepository,
        matrix_service: ISimpleMatrixService,
        storage_mapping: dict[StorageMode, IStudyStorage],
    ):
        self.study_metadata_repo = study_metadata_repo
        self.storage_mapping = storage_mapping
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        logger.info("Getting all matrices used in raw studies")

        study_filter = StudyFilter(
            managed=True, variant=False, archived=False, access_permissions=AccessPermissions(is_admin=True)
        )

        for study in self.study_metadata_repo.get_all(study_filter):
            yield from self.storage_mapping[study.storage_mode].yield_matrix_references(study)
