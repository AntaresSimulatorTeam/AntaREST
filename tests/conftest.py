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
import uuid
from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp
from sqlalchemy.orm import Session

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.favorite.repository import FavoriteDirectoryRepository, FavoriteStudyRepository
from antarest.favorite.service import FavoriteDirectoryService, FavoriteStudyService
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory, ResourcePaths
from antarest.study.model import (
    STUDY_VERSION_7_2,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
    StorageMode,
    Study,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.utils import StudyMetadataCreation, is_managed
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.conftest_db import db_engine_fixture, db_middleware_fixture, db_session_fixture  # noqa: F401
from tests.conftest_instances import admin_user  # noqa: F401

# noinspection PyUnresolvedReferences
from tests.conftest_services import *  # noqa: F403
from tests.helpers import create_raw_study, create_study

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


@pytest.fixture(name="blob_service")
def blob_service_fixture() -> InMemoryBlobService:
    return InMemoryBlobService()


@pytest.fixture(name="favorite_service")
def favorite_service_fixture() -> FavoriteStudyService:
    return FavoriteStudyService(FavoriteStudyRepository())


@pytest.fixture(name="favorite_directory_service")
def favorite_directory_service_fixture() -> FavoriteDirectoryService:
    return FavoriteDirectoryService(FavoriteDirectoryRepository())


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
        districts={},
    )
    # sourcery skip: inline-immediately-returned-variable
    matrix_storage_context = MatrixStorageContext(matrix_service=matrix_service, is_managed=True)

    file_study = FileStudy(
        config=config,
        tree=FileStudyTree(
            matrix_storage_context=matrix_storage_context,
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


@pytest.fixture(name="empty_study_860")
def empty_study_fixture_860(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_6, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_870")
def empty_study_fixture_870(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_7, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_880")
def empty_study_fixture_880(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_8_8, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_920")
def empty_study_fixture_920(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_9_2, matrix_service, tmp_path)


@pytest.fixture(name="empty_study_930")
def empty_study_fixture_930(matrix_service: MatrixService, tmp_path: Path) -> FileStudy:
    return empty_study_fixture(STUDY_VERSION_9_3, matrix_service, tmp_path)


##########################
# DAO
##########################


def build_db_dao(db_session: Session, matrix_service: ISimpleMatrixService, version: StudyVersion) -> DatabaseStudyDao:
    """
    Create a test study in database mode and create a DatabaseStudyDao instance for testing.
    """
    study_id = str(uuid.uuid4())
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    with db_session:
        study = create_study(id=study_id, name="Test Study", version=str(version))
        study.storage_mode = StorageMode.DATABASE
        db_session.add(study)
        db_session.commit()
        factory = DatabaseStudyDaoFactory(matrix_service, generator_matrix_constants, db_session)
        metadata = StudyMetadataCreation(id=study_id, version=version, managed=True)
        dao = factory.create_study_dao(metadata)
    return dao


def build_metadata_creation_object_from_study(study: Study) -> StudyMetadataCreation:
    return StudyMetadataCreation(
        id=study.id,
        version=StudyVersion.parse(study.version),
        managed=is_managed(study),
        name=study.name,
        author=study.author,
        editor=study.editor,
        created_at=study.created_at,
        updated_at=study.updated_at,
    )


def build_filesystem_dao(
    db_session: Session,
    version: StudyVersion,
    command_context: CommandContext,
    study_factory: StudyFactory,
    study_path: Path,
) -> FileStudyTreeDao:
    """
    Create a test study in filesystem mode and create a FileStudyTreeDao instance for testing.
    """
    # Create the path getter method
    study_folder = study_path / "my_study"

    def get_study_path(study_id: str) -> ResourcePaths:
        return ResourcePaths(study_path=study_folder, output_path=study_folder / "output")

    # Create the study
    study_id = str(uuid.uuid4())
    study = create_raw_study(id=study_id, name="Test Study", version=str(version), path=str(study_folder))
    study.storage_mode = StorageMode.FILESYSTEM
    with db_session:
        db_session.add(study)
        db_session.commit()
        factory = FileStudyDaoFactory(command_context, study_factory, Mock(), get_study_path)
        metadata = build_metadata_creation_object_from_study(study)
        dao = factory.create_study_dao(metadata)

    return dao


@pytest.fixture
def db_dao(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def fs_dao(
    db_session: Session, command_context: CommandContext, tmp_path: Path, study_factory: StudyFactory
) -> FileStudyTreeDao:
    return build_filesystem_dao(db_session, STUDY_VERSION_8_8, command_context, study_factory, tmp_path)
