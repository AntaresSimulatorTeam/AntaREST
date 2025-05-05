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


def extract_matrix_id(uri: str) -> str:
    """
    Extract matrix ID from URL matrix://<id>
    """
    return uri.removeprefix(MATRIX_PROTOCOL_PREFIX)


def build_matrix_uri(id: str) -> str:
    return f"{MATRIX_PROTOCOL_PREFIX}{id}"


class MatrixUriMapper:
    """
    In charge of mapping matrix URI to actual data and back.
    """

    def __init__(self, matrix_service: ISimpleMatrixService):
        self._matrix_service = matrix_service

    def get_matrix(self, uri: str) -> pd.DataFrame:
        return self._matrix_service.get(extract_matrix_id(uri))

    def create_matrix(self, matrix: pd.DataFrame) -> str:
        return build_matrix_uri(self._matrix_service.create(matrix))

    def matrix_exists(self, uri: str) -> bool:
        return self._matrix_service.exists(extract_matrix_id(uri))
