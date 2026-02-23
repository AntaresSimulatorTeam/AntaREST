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

import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3, StorageMode
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.helpers import create_study


def build_dao(db_session: Session, matrix_service: ISimpleMatrixService, version: StudyVersion) -> DatabaseStudyDao:
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
        dao = factory.create_study_dao(study)
    return dao


@pytest.fixture
def dao(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def dao_930(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_9_3)


@pytest.fixture
def dao_920(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_dao(db_session, matrix_service, STUDY_VERSION_9_2)
