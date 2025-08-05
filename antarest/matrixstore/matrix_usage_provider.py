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
from abc import ABC, abstractmethod

from antarest.matrixstore.model import MatrixReference


class IMatrixUsageProvider(ABC):
    """
    Provide informations about which matrices are used by a client of the matrix service
    """

    @abstractmethod
    def get_matrix_usage(self) -> list[MatrixReference]:
        raise NotImplementedError()
