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

from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.area import RESERVES_GLOBAL_PARAMETERS_TABLE


def test_get_default_when_no_row(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    area_id = "paris"
    dao.save_area(area_id)

    result = dao.get_reserves_global_parameters(area_id)
    assert result == ReservesGlobalParameters()


def test_save_and_retrieve(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    area_id = "paris"
    dao.save_area(area_id)

    params = ReservesGlobalParameters(
        reference_activation_duration_up=5,
        energy_activation_ratio_up=0.5,
        reference_activation_duration_down=10,
        energy_activation_ratio_down=0.8,
    )
    dao.save_reserves_global_parameters(area_id, params)
    result = dao.get_reserves_global_parameters(area_id)
    assert result == params


def test_save_updates_existing(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    area_id = "paris"
    dao.save_area(area_id)

    params1 = ReservesGlobalParameters(reference_activation_duration_up=5)
    dao.save_reserves_global_parameters(area_id, params1)

    params2 = ReservesGlobalParameters(reference_activation_duration_up=10)
    dao.save_reserves_global_parameters(area_id, params2)

    result = dao.get_reserves_global_parameters(area_id)
    assert result.reference_activation_duration_up == 10


def test_get_all_reserves_global_parameters(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("paris")
    dao.save_area("lyon")

    params_paris = ReservesGlobalParameters(reference_activation_duration_up=5)
    params_lyon = ReservesGlobalParameters(reference_activation_duration_down=10)
    dao.save_reserves_global_parameters("paris", params_paris)
    dao.save_reserves_global_parameters("lyon", params_lyon)

    result = dao.get_all_reserves_global_parameters()
    assert result == {"paris": params_paris, "lyon": params_lyon}


def test_cascade_delete_on_area_removal(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    area_id = "paris"
    dao.save_area(area_id)

    params = ReservesGlobalParameters(reference_activation_duration_up=5)
    dao.save_reserves_global_parameters(area_id, params)

    with db_session:
        dao.delete_area(area_id)
        rows = db_session.execute(select(RESERVES_GLOBAL_PARAMETERS_TABLE)).fetchall()
        assert rows == []
