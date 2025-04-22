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

from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService


class MatrixUriMapper:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service

    def get_matrix(self, uri: str) -> pd.DataFrame:
        matrix_id = self.extract_id(uri)
        return self.matrix_service.get(matrix_id)

    def create_matrix(self, matrix: pd.DataFrame) -> str:
        return self.matrix_service.create(matrix)

    def matrix_exists(self, uri: str) -> bool:
        matrix_id = self.extract_id(uri)
        return self.matrix_service.exists(matrix_id)

    @staticmethod
    def extract_id(uri: str) -> str:
        return uri.removeprefix(MATRIX_PROTOCOL_PREFIX)

    def build_matrix_uri(self, id: str) -> str:
        return f"{MATRIX_PROTOCOL_PREFIX}{id}"
