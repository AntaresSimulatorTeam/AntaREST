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

from antarest.study.business.model.link_model import Link
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import LINK_TABLE


def test_create_link_with_default_properties(db_session: Session, dao: DatabaseStudyDao) -> None:
    study_id = dao.get_study_id()
    dao.save_area("Paris")
    dao.save_area("London")
    link = Link(area1="paris", area2="london")
    dao.save_link(link)

    # Check default Link was created
    stmt = select(LINK_TABLE)
    rows = db_session.execute(stmt).fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert row.study_id == study_id
    assert row.area1 == "london"
    assert row.area2 == "paris"
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
