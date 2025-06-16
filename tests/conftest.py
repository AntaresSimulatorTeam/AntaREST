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

from pathlib import Path
from typing import Callable

import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp

from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import MatrixService
from antarest.study.model import (
    STUDY_VERSION_7_2,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
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


@pytest.fixture(name="matrix_service")
def matrix_service_fixture() -> InMemorySimpleMatrixService:
    return InMemorySimpleMatrixService()


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
    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)

    file_study = FileStudy(
        config=config,
        tree=FileStudyTree(
            matrix_mapper=matrix_mapper,
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
