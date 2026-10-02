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

import polars as pl
import pytest

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.link_model import Link
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _set_up(dao: StudyDao) -> tuple[str, str, pl.DataFrame, pl.DataFrame, Link]:
    matrix_service = dao._matrix_service
    df1 = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series1_id = matrix_service.create(df1)
    df2 = pl.DataFrame(data=[[3, 3], [3, 3]], orient="row")
    series2_id = matrix_service.create(df2)
    area1 = "paris"
    area2 = "london"
    link = Link(area1=area1, area2=area2)

    save_area(dao, area1)
    save_area(dao, area2)
    dao.save_links([link])
    return series1_id, series2_id, df1, df2, link


def test_series_lifecycle(dao: StudyDao) -> None:
    series1_id, series2_id, df1, df2, link = _set_up(dao)

    # Create series
    dao.save_link_series({(link.area1, link.area2): series1_id})

    # Ensures we retrieve the matrix we created
    link_series = dao.get_link_series(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_series, df1, check_dtypes=False)

    # Ensures we cannot set a `link_series` for a fake link
    with pytest.raises(AreaNotFound):
        dao.save_link_series({("fake_area_id", link.area2): series1_id})

    # Ensures we can update an existing matrix
    dao.save_link_series({(link.area1, link.area2): series2_id})
    link_series = dao.get_link_series(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_series, df2, check_dtypes=False)

    # Ensures deleting the link removes it from the study
    dao.delete_link(link)
    assert not dao.link_exists(link.area1, link.area2)


def test_direct_capacity_lifecycle(dao: StudyDao) -> None:
    series1_id, series2_id, df1, df2, link = _set_up(dao)

    # Create direct_capacity matrix
    dao.save_link_direct_capacities({(link.area1, link.area2): series1_id})

    # Ensures we retrieve the matrix we created
    link_direct_capacity = dao.get_link_direct_capacities(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_direct_capacity, df1, check_dtypes=False)

    # Ensures we cannot set a `link_direct_capacity` for a fake link
    with pytest.raises(AreaNotFound):
        dao.save_link_direct_capacities({("fake_area_id", link.area2): series1_id})

    # Ensures we can update an existing matrix
    dao.save_link_direct_capacities({(link.area1, link.area2): series2_id})
    link_direct_capacity = dao.get_link_direct_capacities(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_direct_capacity, df2, check_dtypes=False)

    # Ensures deleting the link removes it from the study
    dao.delete_link(link)
    assert not dao.link_exists(link.area1, link.area2)


def test_indirect_capacity_lifecycle(dao: StudyDao) -> None:
    series1_id, series2_id, df1, df2, link = _set_up(dao)

    # Create indirect_capacity matrix
    dao.save_link_indirect_capacities({(link.area1, link.area2): series1_id})

    # Ensures we retrieve the matrix we created
    link_indirect_capacity = dao.get_link_indirect_capacities(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_indirect_capacity, df1, check_dtypes=False)

    # Ensures we cannot set a `link_indirect_capacity` for a fake link
    with pytest.raises(AreaNotFound):
        dao.save_link_indirect_capacities({("fake_area_id", link.area2): series1_id})

    # Ensures we can update an existing matrix
    dao.save_link_indirect_capacities({(link.area1, link.area2): series2_id})
    link_indirect_capacity = dao.get_link_indirect_capacities(link.area1, link.area2)
    pl.testing.assert_frame_equal(link_indirect_capacity, df2, check_dtypes=False)

    # Ensures deleting the link removes it from the study
    dao.delete_link(link)
    assert not dao.link_exists(link.area1, link.area2)
