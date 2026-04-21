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

import pytest
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7, STUDY_VERSION_8_8, STUDY_VERSION_9_3
from tests.study.dao.conftest import build_db_dao, dao_10_0  # noqa: F401


@pytest.fixture
def db_dao_86(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_6)


@pytest.fixture
def db_dao_87(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_7)


@pytest.fixture
def db_dao_88(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def db_dao_93(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_9_3)
