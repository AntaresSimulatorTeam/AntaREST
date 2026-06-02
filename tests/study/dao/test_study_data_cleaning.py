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

"""
Binding constraint DAO tests, parameterized across both database and filesystem backends.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.area import AREA_TABLE


def test_study_data_cleaning(db_dao_920: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao_920

    # Check the content of the different tables
    with db_session:
        data_container_rows = db_session.execute(select(STUDY_DATA_TABLE)).fetchall()
        assert data_container_rows == [(dao.get_study_id(), dao.get_study_id())]

        area_properties_rows = db_session.execute(select(AREA_TABLE)).fetchall()
        assert area_properties_rows == []

    # Create an area
    dao.save_areas_with_properties({"fr": AreaProperties()})

    # Ensures `AREA_TABLE` is not empty
    with db_session:
        area_properties_rows = db_session.execute(select(AREA_TABLE)).fetchall()
        assert len(area_properties_rows) == 1

    # Empty the `STUDY_DATA_TABLE`
    with db_session:
        db_session.execute(STUDY_DATA_TABLE.delete())
        db_session.commit()

    # Ensures the `AREA_TABLE` was emptied by cascade
    with db_session:
        area_properties_rows = db_session.execute(select(AREA_TABLE)).fetchall()
        assert area_properties_rows == []
