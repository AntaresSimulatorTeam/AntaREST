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
from pathlib import Path

from typing_extensions import override

from antarest.core.config import DEFAULT_WORKSPACE_NAME, Config
from antarest.main import logger
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.repository import StudyFilter, StudyMetadataRepository


class RawStudyMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(
        self, config: Config, study_metadata_repo: StudyMetadataRepository, matrix_service: ISimpleMatrixService
    ):
        self.study_metadata_repo = study_metadata_repo
        self.managed_studies_path: Path = config.storage.workspaces[DEFAULT_WORKSPACE_NAME].path
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> list[MatrixReference]:
        logger.info("Getting all matrices used in raw studies")
        matrices_references = []

        study_filter = StudyFilter(managed=True, variant=False)

        for study in self.study_metadata_repo.get_all(study_filter):
            study_id = study.id
            study_path = Path(study.path)
            for f in study_path.rglob("*.link"):
                matrix_id = extract_matrix_id(f.read_text())
                matrix_reference = MatrixReference(
                    matrix_id=f"{matrix_id}", use_description=f"Used by raw study {study_id}"
                )
                matrices_references.append(matrix_reference)

        # for f in self.managed_studies_path.rglob("*.link"):
        #     matrix_id = extract_matrix_id(f.read_text())
        #     mat_ref = MatrixReference(matrix_id=matrix_id, use_description=f"{matrix}")
        #     matrices_references.append(mat_ref)

        return matrices_references
