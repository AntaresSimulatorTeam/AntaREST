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
from sqlalchemy.orm import Session

from antarest.study.dao.database.database_district_dao import DatabaseDistrictDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import StorageMode
from tests.helpers import create_study


@pytest.fixture
def study_id(db_session: Session) -> str:
    """Create a test study in database mode and return its ID."""
    study_id = str(uuid.uuid4())
    with db_session:
        study = create_study(id=study_id, name="Test Study")
        study.storage_mode = StorageMode.DATABASE
        db_session.add(study)
        db_session.commit()
    return study_id


@pytest.fixture
def dao(db_session: Session, study_id: str) -> DatabaseStudyDao:
    """Create a DatabaseStudyDao instance for testing."""
    return DatabaseStudyDao(study_id, db_session)


@pytest.fixture
def district_dao(db_session: Session, study_id: str) -> DatabaseDistrictDao:
    """Create a DatabaseDistrictDao instance for testing."""
    return DatabaseStudyDao(study_id, db_session)
