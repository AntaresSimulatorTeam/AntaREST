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
from typing_extensions import override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


class ConstantsMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, variant_study_service: VariantStudyService, matrix_service: MatrixService):
        self.matrix_constants = variant_study_service.command_factory.command_context.generator_matrix_constants
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> list[MatrixReference]:
        matrices_references = []
        for value in self.matrix_constants.hashes.values():
            matrix_reference = MatrixReference(matrix_id=value, use_description="")
            matrices_references.append(matrix_reference)

        return matrices_references
