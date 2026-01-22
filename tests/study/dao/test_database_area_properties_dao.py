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

from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import AREA_PROPERTIES_TABLE


def test_save_area_creates_area_with_default_properties(db_session: Session, dao: DatabaseStudyDao) -> None:
    with db_session:
        dao.save_area("Paris")
        db_session.commit()

    with db_session:
        study_id = dao.get_study_id()

        # Check default AreaProperties were created
        stmt_properties = select(AREA_PROPERTIES_TABLE).where(AREA_PROPERTIES_TABLE.c.study_id == study_id)
        row = db_session.execute(stmt_properties).fetchone()
        assert row.study_id == study_id
        assert row.area_id == "paris"
        assert row.energy_cost_unsupplied == 0
        assert row.energy_cost_spilled == 0
        assert row.non_dispatch_power is True
        assert row.dispatch_hydro_power is True
        assert row.other_dispatch_power is True
        assert row.spread_unsupplied_energy_cost == 0
        assert row.spread_spilled_energy_cost == 0
        assert row.filter_synthesis == "hourly, daily, weekly, monthly, annual"
        assert row.filter_by_year == "hourly, daily, weekly, monthly, annual"
        assert row.adequacy_patch_mode is None

    # Ensures we're able to read the data
    properties = dao.get_area_properties(area_id="paris")
    assert properties == AreaProperties()

    # Delete the area to ensure it cascades to properties
    with db_session:
        dao.delete_area("paris")
        db_session.commit()

    assert dao.get_all_area_properties() == {}

    rows = db_session.execute(select(AREA_PROPERTIES_TABLE)).fetchall()
    assert not rows
