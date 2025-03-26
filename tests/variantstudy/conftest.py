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
import typing as t
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import numpy.typing as npt
import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp

from antarest.study.model import STUDY_VERSION_7_2, STUDY_VERSION_8_1, STUDY_VERSION_8_4, STUDY_VERSION_8_7

if t.TYPE_CHECKING:
    # noinspection PyPackageRequirements
    pass

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


def empty_study_fixture(study_version: StudyVersion, matrix_service_2: MatrixService, tmp_path: Path) -> FileStudy:
    """
    Fixture for creating an empty FileStudy object.

    Args:
        study_version: Version of the study to create
        matrix_service: The MatrixService object.
        tmp_path: The temporary path for extracting the empty study.

    Returns:
        FileStudy: The empty FileStudy object.
    """
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path: Path = tmp_path / study_id
    app = CreateApp(study_dir=study_path, caption="empty_study", version=study_version, author="Unknown")
    app()

    config = FileStudyTreeConfig(
        study_path=study_path,
        path=study_path,
        study_id="",
        version=study_version,
        areas={},
        sets={},
    )
    # sourcery skip: inline-immediately-returned-variable
    file_study = FileStudy(
        config=config,
        tree=FileStudyTree(
            context=ContextServer(
                matrix=matrix_service_2,
                resolver=UriResolverService(matrix_service=matrix_service_2),
            ),
            config=config,
        ),
    )
    return file_study


@pytest.fixture(name="empty_study_720")
def empty_study_fixture_720(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_7_2, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_810")
def empty_study_fixture_810(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_1, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_840")
def empty_study_fixture_840(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_4, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_870")
def empty_study_fixture_870(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_7, matrix_service, tmp_path)
