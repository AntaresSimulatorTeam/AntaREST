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
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from typing_extensions import override

from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService

if TYPE_CHECKING:
    from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode


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
    Abstract base class for mapping matrix URIs to actual data and vice versa.

    Defines the interface for URI schema handling related to matrices.
    The expected URI schema is "matrix://<id>", which maps to matrices
    stored in a matrix service.

    Methods to implement:
    - get_matrix: Retrieve a matrix from a URI.
    - create_matrix: Create a matrix and return its URI.
    - matrix_exists: Check if a matrix exists for a given URI.
    - is_managed: Property indicating if the mapper is managed.
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

    @abstractmethod
    def handle_matrix_save(self, data: "MatrixNode", matrix_uri: str, link_path: Path) -> None:
        pass


class BaseMatrixUriMapper(MatrixUriMapper):
    """
    Base implementation of MatrixUriMapper that uses a matrix service
    to perform actual data operations.

    Provides concrete implementations of get_matrix, create_matrix,
    and matrix_exists methods using the underlying matrix service.

    The `is_managed` property remains abstract and should be implemented
    by subclasses to specify if the mapper is managed or unmanaged.
    """

    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self._matrix_service = matrix_service

    @override
    def get_matrix(self, uri: str) -> pd.DataFrame:
        return self._matrix_service.get(extract_matrix_id(uri))

    @override
    def create_matrix(self, matrix: pd.DataFrame) -> str:
        return build_matrix_uri(self._matrix_service.create(matrix))

    @override
    def matrix_exists(self, uri: str) -> bool:
        return self._matrix_service.exists(extract_matrix_id(uri))

    @override
    def handle_matrix_save(self, data: "MatrixNode", matrix_uri: str, link_path: Path) -> None:
        pass


class MatrixUriMapperManaged(BaseMatrixUriMapper):
    """
    Matrix URI mapper for managed matrices.

    """

    @override
    def handle_matrix_save(self, data: "MatrixNode", matrix_uri: str, link_path: Path) -> None:
        link_path.write_text(matrix_uri)
        if data.config.path.exists():
            data.config.path.unlink()


class MatrixUriMapperUnmanaged(BaseMatrixUriMapper):
    """
    Matrix URI mapper for unmanaged matrices.

    Overrides the `is_managed` property to return False.
    """

    @override
    def handle_matrix_save(self, data: "MatrixNode", matrix_uri: str, link_path: Path) -> None:
        matrix = self.get_matrix(matrix_uri)
        data.dump(matrix)


class MatrixUriMapperFactory:
    """
    Factory class responsible for creating instances of MatrixUriMapper.

    Based on the provided MatrixUriMapperType, returns the appropriate
    managed or unmanaged mapper instance.

    Attributes:
        _matrix_service: The matrix service instance to be used by mappers.
    """

    def __init__(self, matrix_service: ISimpleMatrixService):
        self._matrix_service = matrix_service

    def create(self, mapper_type: MatrixUriMapperType = MatrixUriMapperType.MANAGED) -> MatrixUriMapper:
        if mapper_type == MatrixUriMapperType.MANAGED:
            return MatrixUriMapperManaged(self._matrix_service)
        elif mapper_type == MatrixUriMapperType.UNMANAGED:
            return MatrixUriMapperUnmanaged(self._matrix_service)
        else:
            raise ValueError(f"Matrix uri mapper type not supported: {mapper_type}")
