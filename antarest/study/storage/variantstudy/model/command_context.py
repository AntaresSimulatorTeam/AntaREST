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
from pydantic import ConfigDict

from antarest.blobstore.service import IBlobService
from antarest.core.serde import AntaresBaseModel
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


class CommandContext(AntaresBaseModel):
    generator_matrix_constants: GeneratorMatrixConstants
    matrix_service: ISimpleMatrixService
    blob_service: IBlobService

    model_config = ConfigDict(arbitrary_types_allowed=True)
