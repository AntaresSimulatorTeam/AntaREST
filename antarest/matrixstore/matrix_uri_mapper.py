# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import polars as pl
from typing_extensions import override

from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX, ISimpleMatrixService

if TYPE_CHECKING:
    from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode


def extract_matrix_id(uri: str) -> str:
    """
    Extract matrix ID from URL matrix://<id>
    """
    return uri.removeprefix(MATRIX_PROTOCOL_PREFIX)


class NormalizedMatrixUriMapper(StrEnum):
    NORMALIZED = "normalized"
    DENORMALIZED = "denormalized"


def get_mapper_type(with_matrix_normalization: bool) -> NormalizedMatrixUriMapper:
    if with_matrix_normalization:
        return NormalizedMatrixUriMapper.NORMALIZED
    else:
        return NormalizedMatrixUriMapper.DENORMALIZED


def get_path(node: MatrixNode) -> Path:
    return node.config.path.parent / node.config.path.name


class MatrixUriMapper(ABC):
    """
    Abstract base class for mapping matrix URIs to actual data and vice versa.

    Defines the interface for URI schema handling related to matrices.
    The expected URI schema is "matrix://<id>", which maps to matrices
    stored in a matrix service.
    """

    @abstractmethod
    def get_matrix(self, uri: str) -> pl.DataFrame:
        pass

    @abstractmethod
    def matrix_exists(self, uri: str) -> bool:
        pass

    @abstractmethod
    def save_matrix(self, node: MatrixNode, matrix_uri: str) -> None:
        pass

    @abstractmethod
    def delete(self, node: MatrixNode) -> None:
        pass

    @abstractmethod
    def get_link_path(self, node: MatrixNode) -> Path:
        """Returns the path of the .link file associated with the matrix"""
        pass

    @abstractmethod
    def has_link(self, node: MatrixNode) -> bool:
        """Checks if a .link file exists for this matrix"""
        pass

    @abstractmethod
    def get_link_content(self, node: MatrixNode) -> str | None:
        """Returns the content of the .link file if it exists, otherwise None"""
        pass

    @abstractmethod
    def remove_link(self, node: MatrixNode) -> None:
        """Deletes the .link file if it exists"""
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
    def get_matrix(self, uri: str) -> pl.DataFrame:
        return self._matrix_service.get(uri)

    @override
    def matrix_exists(self, uri: str) -> bool:
        return self._matrix_service.exists(uri)

    @override
    def delete(self, node: MatrixNode, url: list[str] | None = None) -> None:
        link_path = Path(f"{get_path(node)}.link")
        if link_path.exists():
            link_path.unlink()

    @override
    def get_link_path(self, node: MatrixNode) -> Path:
        return node.config.path.parent / (node.config.path.name + ".link")

    @override
    def has_link(self, node: MatrixNode) -> bool:
        return self.get_link_path(node).exists()

    @override
    def get_link_content(self, node: MatrixNode) -> str | None:
        link_path = self.get_link_path(node)
        if link_path.exists():
            # Important:
            # in the past, some matrix IDs may have been stored with the "matrix://" prefix,
            # we need to keep that extraction for backwards compat.
            return extract_matrix_id(link_path.read_text())
        return None

    @override
    def remove_link(self, node: MatrixNode) -> None:
        link_path = self.get_link_path(node)
        if link_path.exists():
            link_path.unlink()


class MatrixUriMapperManaged(BaseMatrixUriMapper):
    """
    Matrix URI mapper for managed matrices.

    """

    @override
    def save_matrix(self, node: MatrixNode, matrix_uri: str) -> None:
        link_path = self.get_link_path(node)

        if not link_path.parent.exists():
            # Can happen when creating a new object and the file structure is not yet fully created
            link_path.parent.mkdir(parents=True)

        link_path.write_text(matrix_uri)
        if node.config.path.exists():
            node.config.path.unlink()


class MatrixUriMapperUnmanaged(BaseMatrixUriMapper):
    """
    Matrix URI mapper for unmanaged matrices.

    Overrides the `is_managed` property to return False.
    """

    @override
    def save_matrix(self, node: MatrixNode, matrix_uri: str) -> None:
        matrix = self.get_matrix(matrix_uri)
        node.dump(matrix)


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

    def create(self, mapper_type: NormalizedMatrixUriMapper = NormalizedMatrixUriMapper.NORMALIZED) -> MatrixUriMapper:
        if mapper_type == NormalizedMatrixUriMapper.NORMALIZED:
            return MatrixUriMapperManaged(self._matrix_service)
        elif mapper_type == NormalizedMatrixUriMapper.DENORMALIZED:
            return MatrixUriMapperUnmanaged(self._matrix_service)
        else:
            raise ValueError(f"Matrix uri mapper type not supported: {mapper_type}")
