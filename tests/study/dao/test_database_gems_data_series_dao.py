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

import json

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.data_series import GemsDataSeries
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.data_series import GEMS_DATA_SERIES_TABLE
from tests.study.dao.conftest import build_db_dao_10_2
from tests.study.dao.test_gems_data_series_dao import assert_data_series_equal


def test_data_series_are_isolated_and_deleted_with_study(
    db_session: Session, matrix_service: ISimpleMatrixService
) -> None:
    first_study = build_db_dao_10_2(db_session, matrix_service)
    second_study = build_db_dao_10_2(db_session, matrix_service)
    first_series = GemsDataSeries(id="demand", values=np.array([[1.0], [2.0]]))
    second_series = GemsDataSeries(id="demand", values=np.array([[3.0], [4.0]]))

    first_study.save_data_series([first_series])
    second_study.save_data_series([second_series])
    assert_data_series_equal(first_study.get_data_series(), [first_series])
    assert_data_series_equal(second_study.get_data_series(), [second_series])

    first_study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first_study.get_study_id())
    )
    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == first_study_data_id))
    db_session.commit()

    assert first_study.get_data_series() == []
    assert_data_series_equal(second_study.get_data_series(), [second_series])
    remaining_rows = db_session.execute(select(GEMS_DATA_SERIES_TABLE)).all()
    assert len(remaining_rows) == 1
    assert remaining_rows[0].study_data_id != first_study_data_id


def test_values_are_stored_as_json_encoded_text(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)
    series = GemsDataSeries(id="demand", values=np.array([[1.0, 2.0], [3.0, 4.0]]))

    dao.save_data_series([series])

    row = db_session.execute(select(GEMS_DATA_SERIES_TABLE)).one()
    assert isinstance(row.values, str)
    assert json.loads(row.values) == [[1.0, 2.0], [3.0, 4.0]]


def test_data_series_check_path_traversal_attack(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)

    # Should not write in other folders
    dao.save_data_series([GemsDataSeries(id="../max_load_values", values=np.array([[1, 2, 3]]))])

    data_series = dao.get_data_series()

    assert len(data_series) == 1
    assert data_series[0].id == "max_load_values"
