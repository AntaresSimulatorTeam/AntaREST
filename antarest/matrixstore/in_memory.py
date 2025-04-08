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

import hashlib
import time
from typing import Dict, Optional

import numpy as np
import numpy.typing as npt
import pandas as pd
from typing_extensions import override

from antarest.matrixstore.model import MatrixDTO
from antarest.matrixstore.service import ISimpleMatrixService


class InMemorySimpleMatrixService(ISimpleMatrixService):
    """
    In memory implementation of matrix service, for unit testing purposes.
    """

    def __init__(self) -> None:
        self._content: Dict[str, MatrixDTO] = {}

    def _make_dto(self, id: str, matrix: npt.NDArray[np.float64]) -> MatrixDTO:
        matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
        index = [str(i) for i in range(matrix.shape[0])]
        columns = [str(i) for i in range(matrix.shape[1])]
        return MatrixDTO(
            data=matrix,
            index=index,
            columns=columns,
            id=id,
            created_at=int(time.time()),
            width=len(columns),
            height=len(index),
        )

    @override
    def create(self, data: pd.DataFrame) -> str:
        matrix = np.ascontiguousarray(data.to_numpy())
        matrix_hash = hashlib.sha256(matrix.data).hexdigest()
        self._content[matrix_hash] = self._make_dto(matrix_hash, matrix)
        return matrix_hash

    @override
    def get(self, matrix_id: str) -> Optional[MatrixDTO]:
        return self._content.get(matrix_id, None)

    @override
    def exists(self, matrix_id: str) -> bool:
        return matrix_id in self._content

    @override
    def delete(self, matrix_id: str) -> None:
        del self._content[matrix_id]
