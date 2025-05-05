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
import pandas as pd

from antarest.matrixstore.in_memory import InMemorySimpleMatrixService


def test_matrix_service():
    service = InMemorySimpleMatrixService()
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6]])
    matrix_id = service.create(df)
    assert service.exists(matrix_id)
    created_df = service.get(matrix_id)
    assert created_df.equals(df)
    service.delete(matrix_id)
    assert not service.exists(matrix_id)
