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

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from tests.db_statement_recorder import DBStatementRecorder
from tests.study.dao.utils import save_area


def test_save_area_creates_area_with_default_properties(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    # Ensures we're able to read the data
    properties = dao.get_area_properties(area_id="paris")
    assert properties == AreaProperties()

    # Delete the area to ensure it cascades to properties
    dao.delete_area("paris")

    assert dao.get_all_area_properties() == {}

    rows = dao.get_all_area_ids()
    assert not rows


def test_multiple_areas(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    save_area(dao, "Paris")
    save_area(dao, "London")

    # Ensures we do not perform N+1 requests
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_properties = dao.get_all_area_properties()
        default_props = AreaProperties()
        assert all_properties == {"paris": default_props, "london": default_props}

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


def test_error_cases(dao: StudyDao) -> None:
    # Try to get properties for a fake area
    with pytest.raises(AreaNotFound, match="Area is not found: 'fake_area'"):
        dao.get_area_properties("fake_area")

    # Try to set properties for a fake area
    with pytest.raises(AreaNotFound, match="Area is not found: 'fake_area'"):
        dao.save_area_properties("fake_area", AreaProperties())


def test_modify_properties(dao: StudyDao) -> None:
    area_id = "paris"
    save_area(dao, area_id)

    assert dao.get_area_properties(area_id) == AreaProperties()

    new_properties = AreaProperties(energy_cost_unsupplied=4.5, non_dispatch_power=False, filter_synthesis={"daily"})
    dao.save_area_properties(area_id, new_properties)

    # Ensures we modified the properties accordingly
    assert dao.get_area_properties(area_id) == new_properties
