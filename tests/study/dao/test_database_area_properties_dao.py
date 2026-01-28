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
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import AREA_TABLE
from tests.db_statement_recorder import DBStatementRecorder


def test_save_area_creates_area_with_default_properties(db_session: Session, dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    study_id = dao.get_study_id()

    # Check default AreaProperties were created
    stmt_properties = select(AREA_TABLE).where(AREA_TABLE.c.study_id == study_id)
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
    dao.delete_area("paris")

    assert dao.get_all_area_properties() == {}

    rows = db_session.execute(select(AREA_TABLE)).fetchall()
    assert not rows


def test_multiple_areas(db_session: Session, dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    dao.save_area("London")

    # Ensures we do not perform N+1 requests
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_properties = dao.get_all_area_properties()
        default_props = AreaProperties()
        assert all_properties == {"paris": default_props, "london": default_props}

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


def test_error_cases(dao: DatabaseStudyDao) -> None:
    # Try to get properties for a fake area
    with pytest.raises(AreaNotFound, match="Area is not found: 'fake_area'"):
        dao.get_area_properties("fake_area")

    # Try to set properties for a fake area
    with pytest.raises(AreaNotFound, match="Area is not found: 'fake_area'"):
        dao.save_area_properties("fake_area", AreaProperties())


def test_modify_properties(dao: DatabaseStudyDao) -> None:
    area_id = "paris"
    dao.save_area(area_id)

    assert dao.get_area_properties(area_id) == AreaProperties()

    new_properties = AreaProperties(energy_cost_unsupplied=4.5, non_dispatch_power=False, filter_synthesis={"daily"})
    dao.save_area_properties(area_id, new_properties)

    # Ensures we modified the properties accordingly
    assert dao.get_area_properties(area_id) == new_properties
