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

from antarest.core.exceptions import AreaNotFound, LinkNotFound
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.link_model import DEFAULT_COLOR, AssetType, Link, LinkStyle, TransmissionCapacity
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from tests.db_statement_recorder import DBStatementRecorder
from tests.study.dao.utils import save_area


def _create_default_link(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    save_area(dao, "London")
    dao.save_links([Link(area1="paris", area2="london")])


def test_create_link_with_default_properties(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    save_area(dao, "London")
    link = Link(area1="paris", area2="london")
    dao.save_links([link])

    created_link = dao.get_link("london", "paris")
    assert created_link.area1 == "london"
    assert created_link.area2 == "paris"
    assert created_link.hurdles_cost is False
    assert created_link.loop_flow is False
    assert created_link.use_phase_shifter is False
    assert created_link.transmission_capacities == TransmissionCapacity.ENABLED
    assert created_link.asset_type == AssetType.AC
    assert created_link.display_comments is True
    assert created_link.comments == ""
    assert created_link.colorr == DEFAULT_COLOR
    assert created_link.colorb == DEFAULT_COLOR
    assert created_link.colorg == DEFAULT_COLOR
    assert created_link.link_width == 1.0
    assert created_link.link_style == LinkStyle.PLAIN
    assert list(created_link.filter_synthesis) == [
        FilterOption.HOURLY,
        FilterOption.DAILY,
        FilterOption.WEEKLY,
        FilterOption.MONTHLY,
        FilterOption.ANNUAL,
    ]
    assert list(created_link.filter_year_by_year) == [
        FilterOption.HOURLY,
        FilterOption.DAILY,
        FilterOption.WEEKLY,
        FilterOption.MONTHLY,
        FilterOption.ANNUAL,
    ]
    assert created_link == link


def test_exists_method(dao: StudyDao) -> None:
    # Asserts at first the link does not exist
    assert dao.link_exists("london", "paris") is False

    # Create the link
    _create_default_link(dao)

    # Asserts now it returns `True`
    assert dao.link_exists("london", "paris") is True


def test_get_method(dao: StudyDao) -> None:
    with pytest.raises(LinkNotFound):
        dao.get_link("london", "paris")

    _create_default_link(dao)

    # Should not raise this time
    dao.get_link("london", "paris")


def test_get_all_links(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    dao = db_dao
    _create_default_link(dao)
    save_area(dao, "Berlin")
    dao.save_links([Link(area1="paris", area2="berlin")])

    # Ensures we do not perform N+1 requests
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_links = dao.get_links()
        assert len(all_links) == 2

    assert len(db_recorder.sql_statements) == 1, str(db_recorder)


def test_delete_link(db_dao: DatabaseStudyDao) -> None:
    link = Link(area1="paris", area2="london")
    with pytest.raises(LinkNotFound):
        db_dao.delete_link(link)

    _create_default_link(db_dao)

    # Delete the existing link
    db_dao.delete_link(link)

    # Asserts there are no links left in DB
    rows = db_dao.get_links()
    assert rows == []


def test_save_link(dao: StudyDao) -> None:
    _create_default_link(dao)

    # Save the link with new properties
    new_link = Link(
        area1="paris", area2="london", hurdles_cost=True, comments="My link", filter_synthesis=[FilterOption.DAILY]
    )
    dao.save_links([new_link])

    # Asserts the properties were well modified
    link = dao.get_link("london", "paris")
    assert link == new_link

    # Create a link with wrong area and ensure we raise a clear exception
    with pytest.raises(AreaNotFound):
        dao.save_links([Link(area1="paris", area2="fake_area")])


def test_save_link_filters_propagate_to_synthesis(dao: StudyDao) -> None:
    """`save_links` must propagate filters into the in-memory link config exposed by
    `get_synthesis`"""
    save_area(dao, "Paris")
    save_area(dao, "London")

    dao.save_links(
        [
            Link(
                area1="paris",
                area2="london",
                filter_synthesis=[FilterOption.DAILY, FilterOption.WEEKLY],
                filter_year_by_year=[FilterOption.HOURLY],
            )
        ]
    )

    link_config = dao.get_synthesis().areas["london"].links["paris"]
    assert link_config.filters_synthesis == ["daily", "weekly"]
    assert link_config.filters_year == ["hourly"]


def test_delete_area(dao: StudyDao) -> None:
    _create_default_link(dao)
    save_area(dao, "Toulouse")
    dao.save_links([Link(area1="paris", area2="toulouse")])

    # Removing the area `Paris` should remove the 2 links as they both reference it.
    # For one link, it's `area2` and for the other `area1`
    dao.delete_area("paris")

    rows = dao.get_links()
    assert rows == []
