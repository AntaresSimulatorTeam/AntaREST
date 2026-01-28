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
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import (
    LOAD_TABLE,
    MISC_GEN_TABLE,
    RESERVES_TABLE,
    SOLAR_TABLE,
    WIND_TABLE,
)


def test_load_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)
    dao.save_load(area_id, series_id)

    # Ensures we retrieve the load we created
    load = dao.get_load(area_id)
    pl.testing.assert_frame_equal(load, dataframe, check_dtypes=False)

    # Ensures we cannot set a load for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_load("fake_area_id", series_id)

    # Ensures deleting the area deletes the row from `Load` table
    with db_session:
        dao.delete_area(area_id)

        load_rows = db_session.execute(select(LOAD_TABLE)).fetchall()
        assert load_rows == []


def test_solar_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)
    dao.save_solar(area_id, series_id)

    # Ensures we retrieve the solar matrix we created
    solar = dao.get_solar(area_id)
    pl.testing.assert_frame_equal(solar, dataframe, check_dtypes=False)

    # Ensures we cannot set a solar matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_solar("fake_area_id", series_id)

    # Ensures deleting the area deletes the row from `Solar` table
    with db_session:
        dao.delete_area(area_id)

        solar_rows = db_session.execute(select(SOLAR_TABLE)).fetchall()
        assert solar_rows == []


def test_wind_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)
    dao.save_wind(area_id, series_id)

    # Ensures we retrieve the wind matrix we created
    wind = dao.get_wind(area_id)
    pl.testing.assert_frame_equal(wind, dataframe, check_dtypes=False)

    # Ensures we cannot set a wind matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_wind("fake_area_id", series_id)

    # Ensures deleting the area deletes the row from `Wind` table
    with db_session:
        dao.delete_area(area_id)

        wind_rows = db_session.execute(select(WIND_TABLE)).fetchall()
        assert wind_rows == []


def test_reserves_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)
    dao.save_reserves(area_id, series_id)

    # Ensures we retrieve the reserves matrix we created
    reserves = dao.get_reserves(area_id)
    pl.testing.assert_frame_equal(reserves, dataframe, check_dtypes=False)

    # Ensures we cannot set a reserves matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_reserves("fake_area_id", series_id)

    # Ensures deleting the area deletes the row from `Reserves` table
    with db_session:
        dao.delete_area(area_id)

        reserves_rows = db_session.execute(select(RESERVES_TABLE)).fetchall()
        assert reserves_rows == []


def test_misc_gen_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)
    dao.save_misc_gen(area_id, series_id)

    # Ensures we retrieve the misc-gen matrix we created
    misc_gen = dao.get_misc_gen(area_id)
    pl.testing.assert_frame_equal(misc_gen, dataframe, check_dtypes=False)

    # Ensures we cannot set a misc-gen matrix for a fake area
    with pytest.raises(AreaNotFound):
        dao.save_misc_gen("fake_area_id", series_id)

    # Ensures deleting the area deletes the row from `misc-gen` table
    with db_session:
        dao.delete_area(area_id)

        misc_gen_rows = db_session.execute(select(MISC_GEN_TABLE)).fetchall()
        assert misc_gen_rows == []


def test_garbage_collection(dao: DatabaseStudyDao) -> None:
    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)
    area_id = "paris"

    dao.save_area(area_id)

    # Create `load`, `solar`, `wind`, `reserves` and `misc-gen` matrices in DB
    dao.save_load(area_id, series_id)
    dao.save_solar(area_id, series_id)
    dao.save_wind(area_id, series_id)
    dao.save_reserves(area_id, series_id)
    dao.save_misc_gen(area_id, series_id)

    # Launch the Garbage collection
    task = clean_matrices(matrix_service=matrix_service, dry_run=False, retention_time=0)
    assert task.status == BackGroundTaskStatus.SUCCESS
    assert task.deleted_count == 0

    # Ensures the matrices were not removed from their tables
    load = dao.get_load(area_id)
    pl.testing.assert_frame_equal(load, dataframe, check_dtypes=False)

    solar = dao.get_solar(area_id)
    pl.testing.assert_frame_equal(solar, dataframe, check_dtypes=False)

    wind = dao.get_wind(area_id)
    pl.testing.assert_frame_equal(wind, dataframe, check_dtypes=False)

    misc_gen = dao.get_misc_gen(area_id)
    pl.testing.assert_frame_equal(misc_gen, dataframe, check_dtypes=False)

    reserves = dao.get_reserves(area_id)
    pl.testing.assert_frame_equal(reserves, dataframe, check_dtypes=False)
