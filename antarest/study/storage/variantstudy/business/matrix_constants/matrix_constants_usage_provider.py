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
from typing import Iterable

from typing_extensions import TYPE_CHECKING, override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService

if TYPE_CHECKING:
    from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


class ConstantsMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, matrix_constants: "GeneratorMatrixConstants", matrix_service: ISimpleMatrixService):
        self.matrix_constants = matrix_constants
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        for value in self.matrix_constants.hashes.values():
            yield MatrixReference(matrix_id=value, use_description="Constant matrix")
