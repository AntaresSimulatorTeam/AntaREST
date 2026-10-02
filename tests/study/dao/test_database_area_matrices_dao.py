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
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def test_load_lifecycle(dao: StudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    save_area(dao, area_id)
    dao.save_load({area_id: series_id})

    # Ensures we retrieve the load we created
    load = dao.get_load(area_id)
    pl.testing.assert_frame_equal(load, dataframe, check_dtypes=False)

    # Ensures we cannot set a load for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_load({"fake_area_id": series_id})

    # Ensures deleting the area deletes the load
    dao.delete_area(area_id)
    with pytest.raises(AreaNotFound):
        dao.get_load(area_id)


def test_solar_lifecycle(dao: StudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    save_area(dao, area_id)
    dao.save_solar({area_id: series_id})

    # Ensures we retrieve the solar matrix we created
    solar = dao.get_solar(area_id)
    pl.testing.assert_frame_equal(solar, dataframe, check_dtypes=False)

    # Ensures we cannot set a solar matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_solar({"fake_area_id": series_id})

    # Ensures deleting the area deletes the solar matrix
    dao.delete_area(area_id)
    with pytest.raises(AreaNotFound):
        dao.get_solar(area_id)


def test_wind_lifecycle(dao: StudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    save_area(dao, area_id)
    dao.save_wind({area_id: series_id})

    # Ensures we retrieve the wind matrix we created
    wind = dao.get_wind(area_id)
    pl.testing.assert_frame_equal(wind, dataframe, check_dtypes=False)

    # Ensures we cannot set a wind matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_wind({"fake_area_id": series_id})

    # Ensures deleting the area deletes the wind matrix
    dao.delete_area(area_id)
    with pytest.raises(AreaNotFound):
        dao.get_wind(area_id)


def test_reserves_lifecycle(dao: StudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    save_area(dao, area_id)
    dao.save_reserves({area_id: series_id})

    # Ensures we retrieve the reserves matrix we created
    reserves = dao.get_reserves(area_id)
    pl.testing.assert_frame_equal(reserves, dataframe, check_dtypes=False)

    # Ensures we cannot set a reserves matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_reserves({"fake_area_id": series_id})

    # Ensures deleting the area deletes the reserves matrix
    dao.delete_area(area_id)
    with pytest.raises(AreaNotFound):
        dao.get_reserves(area_id)


def test_misc_gen_lifecycle(dao: StudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    save_area(dao, area_id)
    dao.save_misc_gen({area_id: series_id})

    # Ensures we retrieve the misc-gen matrix we created
    misc_gen = dao.get_misc_gen(area_id)
    pl.testing.assert_frame_equal(misc_gen, dataframe, check_dtypes=False)

    # Ensures we cannot set a misc-gen matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_misc_gen({"fake_area_id": series_id})

    # Ensures deleting the area deletes the misc-gen matrix
    dao.delete_area(area_id)
    with pytest.raises(AreaNotFound):
        dao.get_misc_gen(area_id)
