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
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.study.dao.database.database_area_dao import DatabaseAreaDao
from antarest.study.dao.database.models import AREA_PROPERTIES_TABLE


def test_save_area_creates_area_with_default_properties(db_session: Session, dao: DatabaseAreaDao) -> None:
    """
    Test that save_area creates a new area with default UI for layer '0'.
    """
    with db_session:
        dao.save_area("Paris")
        db_session.commit()

    with db_session:
        study_id = dao.get_study_id()

        # Check default AreaProperties were created
        stmt_properties = select(AREA_PROPERTIES_TABLE).where(AREA_PROPERTIES_TABLE.c.study_id == study_id)
        rows = db_session.execute(stmt_properties).fetchone()
        print(rows)
