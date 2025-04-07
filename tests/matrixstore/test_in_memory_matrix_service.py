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
import numpy as np

from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.model import MatrixDTO


def test_matrix_service():
    service = InMemorySimpleMatrixService()
    matrix_id = service.create([[1, 2, 3], [4, 5, 6]])
    assert service.exists(matrix_id)
    dto = service.get(matrix_id)
    assert dto == MatrixDTO(
        id=matrix_id,
        data=np.array([[1, 2, 3], [4, 5, 6]]),
        index=["0", "1"],
        columns=["0", "1", "2"],
        width=3,
        height=2,
        created_at=dto.created_at,
    )
    service.delete(matrix_id)
    assert not service.exists(matrix_id)
