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

from antarest.core.exceptions import AreaNotFound, LinkNotFound
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.link_model import DEFAULT_COLOR, AssetType, Link, LinkStyle, TransmissionCapacity
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.link import LINK_TABLE
from tests.db_statement_recorder import DBStatementRecorder


def _create_default_link(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    dao.save_area("London")
    link = Link(area1="paris", area2="london")
    dao.save_link(link)


def test_create_link_with_default_properties(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
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
    assert row.hurdles_cost is False
    assert row.loop_flow is False
    assert row.use_phase_shifter is False
    assert row.transmission_capacities == TransmissionCapacity.ENABLED
    assert row.asset_type == AssetType.AC
    assert row.display_comments is True
    assert row.comments == ""
    assert row.colorr == DEFAULT_COLOR
    assert row.colorb == DEFAULT_COLOR
    assert row.colorg == DEFAULT_COLOR
    assert row.link_width == 1.0
    assert row.link_style == LinkStyle.PLAIN
    assert row.filter_synthesis == "hourly, daily, weekly, monthly, annual"
    assert row.filter_year_by_year == "hourly, daily, weekly, monthly, annual"

    # Check the return method
    created_link = dao.get_link("london", "paris")
    assert created_link == link


def test_exists_method(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    # Asserts at first the link does not exist
    assert dao.link_exists("london", "paris") is False

    # Create the link
    _create_default_link(dao)

    # Asserts now it returns `True`
    assert dao.link_exists("london", "paris") is True


def test_get_method(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    with pytest.raises(LinkNotFound):
        dao.get_link("london", "paris")

    _create_default_link(dao)

    # Should not raise this time
    dao.get_link("london", "paris")


def test_get_all_links(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao
    _create_default_link(dao)
    dao.save_area("Berlin")
    dao.save_link(Link(area1="paris", area2="berlin"))

    # Ensures we do not perform N+1 requests
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_links = dao.get_links()
        assert len(all_links) == 2

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


def test_delete_link(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao
    link = Link(area1="paris", area2="london")
    with pytest.raises(LinkNotFound):
        dao.delete_link(link)

    _create_default_link(dao)

    # Delete the existing link
    dao.delete_link(link)

    # Asserts there are no links left in DB
    stmt = select(LINK_TABLE)
    rows = db_session.execute(stmt).fetchall()
    assert rows == []


def test_save_link(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    _create_default_link(dao)

    # Save the link with new properties
    new_link = Link(
        area1="paris", area2="london", hurdles_cost=True, comments="My link", filter_synthesis=[FilterOption.DAILY]
    )
    dao.save_link(new_link)

    # Asserts the properties were well modified
    link = dao.get_link("london", "paris")
    assert link == new_link

    # Create a link with wrong area and ensure we raise a clear exception
    with pytest.raises(AreaNotFound):
        dao.save_link(Link(area1="paris", area2="fake_area"))


def test_delete_area(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao
    _create_default_link(dao)
    dao.save_area("Toulouse")
    dao.save_link(Link(area1="paris", area2="toulouse"))

    # Removing the area `Paris` should remove the 2 links as they both reference it.
    # For one link, it's `area2` and for the other `area1`
    dao.delete_area("paris")

    stmt = select(LINK_TABLE)
    rows = db_session.execute(stmt).fetchall()
    assert rows == []
