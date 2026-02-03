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
from pathlib import Path
from unittest.mock import Mock

import polars as pl
from sqlalchemy.orm import Session

from antarest.core.config import InternalMatrixFormat
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.gc_matrix import clean_matrices
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.business.model.link_model import Link
from antarest.study.dao.database.database_matrices_provider import StudyDatabaseMatrixUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_garbage_collection(dao: DatabaseStudyDao, db_session: Session, tmp_path: Path) -> None:
    # Create a real matrix_service
    bucket_dir = tmp_path / "matrix_store"
    matrix_service = MatrixService(
        repo=MatrixRepository(db_session),
        repo_dataset=MatrixDataSetRepository(db_session),
        matrix_content_repository=MatrixContentRepository(bucket_dir, InternalMatrixFormat.FEATHER),
        file_transfer_manager=Mock(),
        task_service=Mock(),
        config=Mock(),
        user_service=Mock(),
    )
    dao._matrix_service = matrix_service

    # Register the DB provider
    provider = StudyDatabaseMatrixUsageProvider(matrix_service)
    matrix_service.register_usage_provider(provider)

    # Create a matrix in the matrix-store
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    # Create `load`, `solar`, `wind`, `reserves` and `misc-gen` matrices in DB
    area_id = "paris"
    dao.save_area(area_id)
    dao.save_load(area_id, series_id)
    dao.save_solar(area_id, series_id)
    dao.save_wind(area_id, series_id)
    dao.save_reserves(area_id, series_id)
    dao.save_misc_gen(area_id, series_id)

    # Also create a link with `series`, `direct_capacity` and `indirect_capacity` matrices.
    area2 = "london"
    dao.save_area(area2)
    dao.save_link(Link(area1=area_id, area2=area2))
    dao.save_link_series(area_id, area2, series_id)
    dao.save_link_direct_capacities(area_id, area2, series_id)
    dao.save_link_indirect_capacities(area_id, area2, series_id)

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

    link_series = dao.get_link_series(area_id, area2)
    pl.testing.assert_frame_equal(link_series, dataframe, check_dtypes=False)

    link_direct_capacity = dao.get_link_direct_capacities(area_id, area2)
    pl.testing.assert_frame_equal(link_direct_capacity, dataframe, check_dtypes=False)

    link_indirect_capacity = dao.get_link_indirect_capacities(area_id, area2)
    pl.testing.assert_frame_equal(link_indirect_capacity, dataframe, check_dtypes=False)
