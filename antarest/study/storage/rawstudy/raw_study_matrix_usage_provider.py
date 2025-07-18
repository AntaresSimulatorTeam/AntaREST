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
from antarest.matrixstore.service import MatrixService


class RawStudyMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, config: Config, matrix_service: MatrixService):
        self.managed_studies_path: Path = config.storage.workspaces[DEFAULT_WORKSPACE_NAME].path
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> list[MatrixReference]:
        # renvoyer la même chose que le get_matrices associé
        logger.info("Getting all matrices used in raw studies")
        matrices_references = []
        for f in self.managed_studies_path.rglob("*.link"):
            matrix_id = extract_matrix_id(f.read_text())
            mat_ref = MatrixReference(matrix_id=matrix_id, use_description="")
            matrices_references.append(mat_ref)

        return matrices_references
