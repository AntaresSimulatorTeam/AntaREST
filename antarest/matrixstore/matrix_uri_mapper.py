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
from enum import StrEnum

import pandas as pd
from typing_extensions import override

from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService


def extract_matrix_id(uri: str) -> str:
    """
    Extract matrix ID from URL matrix://<id>
    """
    return uri.removeprefix(MATRIX_PROTOCOL_PREFIX)


def build_matrix_uri(id: str) -> str:
    return f"{MATRIX_PROTOCOL_PREFIX}{id}"


class MatrixUriMapperType(StrEnum):
    MANAGED = "managed"
    UNMANAGED = "unmanaged"


def get_mapper_type(is_managed: bool) -> MatrixUriMapperType:
    if is_managed:
        return MatrixUriMapperType.MANAGED
    else:
        return MatrixUriMapperType.UNMANAGED


class MatrixUriMapper(ABC):
    """
    In charge of mapping matrix URI to actual data and back.

    The only actual URI schema supported is "matrix://<id>", which
    maps to a matrix stored in the matrix service.
    """

    @abstractmethod
    def get_matrix(self, uri: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def create_matrix(self, matrix: pd.DataFrame) -> str:
        pass

    @abstractmethod
    def matrix_exists(self, uri: str) -> bool:
        pass


class MatrixUriMapperManaged(MatrixUriMapper):
    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self._matrix_service = matrix_service

    @override
    def get_matrix(self, uri: str) -> pd.DataFrame:
        print("MANAGED")
        return self._matrix_service.get(extract_matrix_id(uri))

    @override
    def create_matrix(self, matrix: pd.DataFrame) -> str:
        print("MANAGED")
        return build_matrix_uri(self._matrix_service.create(matrix))

    @override
    def matrix_exists(self, uri: str) -> bool:
        print("MANAGED")
        return self._matrix_service.exists(extract_matrix_id(uri))


class MatrixUriMapperUnmanaged(MatrixUriMapper):
    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self._matrix_service = matrix_service

    @override
    def get_matrix(self, uri: str) -> pd.DataFrame:
        print("UNMANAGED")
        return self._matrix_service.get(extract_matrix_id(uri))

    @override
    def create_matrix(self, matrix: pd.DataFrame) -> str:
        print("UNMANAGED")
        return build_matrix_uri(self._matrix_service.create(matrix))

    @override
    def matrix_exists(self, uri: str) -> bool:
        print("UNMANAGED")
        return self._matrix_service.exists(extract_matrix_id(uri))


class MatrixUriMapperFactory:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self._matrix_service = matrix_service

    def create(self, mapper_type: MatrixUriMapperType = MatrixUriMapperType.MANAGED) -> MatrixUriMapper:
        if mapper_type == MatrixUriMapperType.MANAGED:
            return MatrixUriMapperManaged(self._matrix_service)
        elif mapper_type == MatrixUriMapperType.UNMANAGED:
            return MatrixUriMapperUnmanaged(self._matrix_service)
        else:
            raise ValueError(f"Matrix uri mapper type not supported: {mapper_type}")
