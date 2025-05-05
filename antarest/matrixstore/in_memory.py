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

from typing import Dict

import pandas as pd
from typing_extensions import override

from antarest.matrixstore.repository import compute_hash
from antarest.matrixstore.service import ISimpleMatrixService, MatrixProvider


class InMemorySimpleMatrixService(ISimpleMatrixService):
    """
    In memory implementation of matrix service, for unit testing purposes.
    """

    def __init__(self) -> None:
        self._content: Dict[str, pd.DataFrame] = {}
        self._providers: dict[str, MatrixProvider] = {}

    @override
    def add_provider(self, provider: MatrixProvider) -> str:
        matrix_hash = compute_hash(provider())
        self._providers[matrix_hash] = provider
        return matrix_hash

    @override
    def create(self, data: pd.DataFrame) -> str:
        matrix_hash = compute_hash(data)
        self._content[matrix_hash] = data
        return matrix_hash

    @override
    def get(self, matrix_id: str) -> pd.DataFrame:
        if matrix_id in self._providers:
            return self._providers[matrix_id]()
        return self._content[matrix_id]

    @override
    def exists(self, matrix_id: str) -> bool:
        return matrix_id in self._providers or matrix_id in self._content

    @override
    def delete(self, matrix_id: str) -> None:
        if matrix_id in self._providers:
            del self._providers[matrix_id]
        del self._content[matrix_id]
