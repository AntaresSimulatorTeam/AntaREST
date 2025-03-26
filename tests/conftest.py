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
from pathlib import Path
from typing import Callable, Union
from unittest.mock import Mock

import numpy as np
import numpy.typing as npt
import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp

from antarest.matrixstore.model import MatrixDTO
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.model import (
    STUDY_VERSION_7_2,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from tests.conftest_db import db_engine_fixture, db_middleware_fixture, db_session_fixture  # noqa: F401
from tests.conftest_instances import admin_user  # noqa: F401

# noinspection PyUnresolvedReferences
from tests.conftest_services import *  # noqa: F403

HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))


@pytest.fixture(scope="session")
def project_path() -> Path:
    return PROJECT_DIR


@pytest.fixture
def ini_cleaner() -> Callable[[str], str]:
    def cleaner(txt: str) -> str:
        lines = filter(None, map(str.strip, txt.splitlines(keepends=False)))
        return "\n".join(lines)

    return cleaner


@pytest.fixture
def clean_ini_writer(ini_cleaner: Callable[[str], str]) -> Callable[[Path, str], None]:
    def write_clean_ini(path: Path, txt: str) -> None:
        clean_ini = ini_cleaner(txt)
        path.write_text(clean_ini)

    return write_clean_ini


@pytest.fixture(name="matrix_service")
def matrix_service_fixture() -> MatrixService:
    """
    Fixture for creating a mocked matrix service.

    Returns:
        An instance of the `SimpleMatrixService` class representing the matrix service.
    """

    matrix_map: dict[str, npt.NDArray[np.float64]] = {}

    def create(data: Union[list[list[float]], npt.NDArray[np.float64]]) -> str:
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

    def get_matrix_id(matrix: Union[list[list[float]], str]) -> str:
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


def empty_study_fixture(study_version: StudyVersion, matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    """
    Fixture for creating an empty FileStudy object.

    Args:
        study_version: Version of the study to create
        matrix_service: The MatrixService object.
        tmp_path: The temporary path for extracting the empty study.

    Returns:
        FileStudy: The empty FileStudy object.
    """
    study_id = f"study_id_{study_version}"
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
                matrix=matrix_service,
                resolver=UriResolverService(matrix_service=matrix_service),
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


@pytest.fixture(name="empty_study_880")
def empty_study_fixture_880(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_8, matrix_service, tmp_path)
