# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from typing_extensions import Iterable, override

from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.repository import AccessPermissions, StudyFilter, StudyMetadataRepository

logger = logging.getLogger(__name__)


class RawStudyMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, study_metadata_repo: StudyMetadataRepository, matrix_service: ISimpleMatrixService):
        self.study_metadata_repo = study_metadata_repo
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        logger.info("Getting all matrices used in raw studies")

        study_filter = StudyFilter(
            managed=True, variant=False, archived=False, access_permissions=AccessPermissions(is_admin=True)
        )

        for study in self.study_metadata_repo.get_all(study_filter):
            study_id = study.id
            study_path = Path(study.path)
            # Only check `input` and `user/expansion` path as they are the only folders capable of having `.link` files.
            for path in [study_path / "input", study_path / "user" / "expansion"]:
                for f in path.rglob("*.link"):
                    matrix_id = extract_matrix_id(f.read_text())
                    matrix_reference = MatrixReference(
                        matrix_id=f"{matrix_id}", use_description=f"Used by raw study {study_id}"
                    )
                    yield matrix_reference
