# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from pydantic import BaseModel

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


class CommandContext(BaseModel):
    generator_matrix_constants: GeneratorMatrixConstants
    matrix_service: ISimpleMatrixService
    patch_service: PatchService

    class Config:
        arbitrary_types_allowed = True
