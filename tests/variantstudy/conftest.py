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
import re
import typing as t
import zipfile
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import numpy.typing as npt
import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import StudyValidationError

if t.TYPE_CHECKING:
    # noinspection PyPackageRequirements
    from _pytest.fixtures import SubRequest

from antarest.matrixstore.model import MatrixDTO
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.assets import ASSETS_DIR


@pytest.fixture(name="matrix_service")
def matrix_service_fixture() -> MatrixService:
    """
    Fixture for creating a mocked matrix service.

    Returns:
        An instance of the `SimpleMatrixService` class representing the matrix service.
    """

    matrix_map: t.Dict[str, npt.NDArray[np.float64]] = {}

    def create(data: t.Union[t.List[t.List[float]], npt.NDArray[np.float64]]) -> str:
        """
        This function calculates a unique ID for each matrix, without storing
        any data in the file system or the database.
        """
        matrix = data if isinstance(data, np.ndarray) else np.array(data, dtype=np.float64)
        matrix_hash = hashlib.sha256(matrix.data).hexdigest()
        matrix_map[matrix_hash] = matrix
        return matrix_hash

    def get(matrix_id: str) -> MatrixDTO:
        """
        This function retrieves the matrix from the map.
        """
        data = matrix_map[matrix_id]
        return MatrixDTO(
            id=matrix_id,
            width=data.shape[1],
            height=data.shape[0],
            index=[str(i) for i in range(data.shape[0])],
            columns=[str(i) for i in range(data.shape[1])],
            data=data.tolist(),
        )

    def exists(matrix_id: str) -> bool:
        """
        This function checks if the matrix exists in the map.
        """
        return matrix_id in matrix_map

    def delete(matrix_id: str) -> None:
        """
        This function deletes the matrix from the map.
        """
        del matrix_map[matrix_id]

    def get_matrix_id(matrix: t.Union[t.List[t.List[float]], str]) -> str:
        """
        Get the matrix ID from a matrix or a matrix link.
        """
        if isinstance(matrix, str):
            return matrix.removeprefix("matrix://")
        elif isinstance(matrix, list):
            return create(matrix)
        else:
            raise TypeError(f"Invalid type for matrix: {type(matrix)}")

    matrix_service = Mock(spec=MatrixService)
    matrix_service.create.side_effect = create
    matrix_service.get.side_effect = get
    matrix_service.exists.side_effect = exists
    matrix_service.delete.side_effect = delete
    matrix_service.get_matrix_id.side_effect = get_matrix_id

    return matrix_service


@pytest.fixture(name="command_context")
def command_context_fixture(matrix_service: MatrixService) -> CommandContext:
    """
    Fixture for creating a CommandContext object.

    Args:
        matrix_service: The MatrixService object.

    Returns:
        CommandContext: The CommandContext object.
    """
    # sourcery skip: inline-immediately-returned-variable
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    command_context = CommandContext(
        generator_matrix_constants=generator_matrix_constants,
        matrix_service=matrix_service,
    )
    return command_context


@pytest.fixture(name="command_factory")
def command_factory_fixture(matrix_service: MatrixService) -> CommandFactory:
    """
    Fixture for creating a CommandFactory object.

    Args:
        matrix_service: The MatrixService object.

    Returns:
        CommandFactory: The CommandFactory object.
    """
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    return CommandFactory(
        generator_matrix_constants=generator_matrix_constants,
        matrix_service=matrix_service,
    )


@pytest.fixture(name="empty_study")
def empty_study_fixture(request: "SubRequest", tmp_path: Path, matrix_service: MatrixService) -> FileStudy:
    """
    Fixture for creating an empty FileStudy object.

    Args:
        request: pytest's request object.
        tmp_path: The temporary path for extracting the empty study.
        matrix_service: The MatrixService object.

    Returns:
        FileStudy: The empty FileStudy object.
    """
    zip_name = getattr(request, "param", "empty_study_720.zip")
    empty_study_path: Path = ASSETS_DIR / zip_name
    empty_study_destination_path = tmp_path.joinpath("empty-study")
    with zipfile.ZipFile(empty_study_path, "r") as zip_empty_study:
        zip_empty_study.extractall(empty_study_destination_path)

    # Detect the version of the study from `study.antares` file.
    version = _get_current_version(empty_study_destination_path)

    config = FileStudyTreeConfig(
        study_path=empty_study_destination_path,
        path=empty_study_destination_path,
        study_id="",
        version=StudyVersion.parse(version),
        areas={},
        sets={},
    )
    # sourcery skip: inline-immediately-returned-variable
    file_study = FileStudy(
        config=config,
        tree=FileStudyTree(
            context=ContextServer(
                matrix=matrix_service,
                resolver=UriResolverService(matrix_service=matrix_service),
            ),
            config=config,
        ),
    )
    return file_study


def _get_current_version(study_path: Path) -> str:
    antares_path = study_path / "study.antares"
    pattern = r"version\s*=\s*([\w.-]+)\s*"
    with antares_path.open(encoding="utf-8") as lines:
        for line in lines:
            if match := re.fullmatch(pattern, line):
                return match[1].rstrip()
    raise StudyValidationError(
        f"File parsing error: the version number is not found in '{antares_path}'"
        f" or does not match the expected '{pattern}' format."
    )
