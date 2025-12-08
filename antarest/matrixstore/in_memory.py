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

from typing import Dict, Iterator, List

import pandas as pd
from typing_extensions import override

from antarest.matrixstore.matrix_usage_provider import IMatrixUsageProvider
from antarest.matrixstore.model import MatrixMetadataDTO, MatrixReferencesDTO
from antarest.matrixstore.repository import compute_hash
from antarest.matrixstore.service import ISimpleMatrixService


class InMemorySimpleMatrixService(ISimpleMatrixService):
    """
    In memory implementation of matrix service, for unit testing purposes.
    """

    def __init__(self) -> None:
        self._content: Dict[str, pd.DataFrame] = {}
        self.usage_providers: List[IMatrixUsageProvider] = []

    @override
    def create(self, data: pd.DataFrame) -> str:
        matrix_hash = compute_hash(data)
        self._content[matrix_hash] = data
        return matrix_hash

    @override
    def create_batch(self, data: Iterator[pd.DataFrame]) -> list[str]:
        return [self.create(df) for df in data]

    @override
    def get(self, matrix_id: str) -> pd.DataFrame:
        return self._content[matrix_id]

    @override
    def exists(self, matrix_id: str) -> bool:
        return matrix_id in self._content

    @override
    def delete(self, matrix_id: str) -> None:
        del self._content[matrix_id]

    @override
    def register_usage_provider(self, usage_provider: IMatrixUsageProvider) -> None:
        self.usage_providers.append(usage_provider)

    @override
    def get_matrices(self) -> list[MatrixMetadataDTO]:
        raise NotImplementedError()

    @override
    def get_matrices_references(self, disk_usage: bool) -> dict[str, MatrixReferencesDTO]:
        raise NotImplementedError()
