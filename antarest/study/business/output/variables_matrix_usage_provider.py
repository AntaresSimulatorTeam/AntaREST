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

from typing_extensions import Iterable, override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService

logger = logging.getLogger(__name__)


class OutputVariablesMatrixUsageProvider(IMatrixUsageProvider):
    def __init__(self, matrix_service: ISimpleMatrixService):
        matrix_service.register_usage_provider(self)

    @override
    def get_matrix_usage(self) -> Iterable[MatrixReference]:
        logger.info("Getting all matrices used in output variables views")
        with db():
            return []
