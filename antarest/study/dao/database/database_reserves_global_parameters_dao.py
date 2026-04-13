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

"""
Database implementation of ReservesGlobalParametersDao using SQLAlchemy Core.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.api.reserves_global_parameters_dao import ReservesGlobalParametersDao
from antarest.study.dao.database.models.area import RESERVES_GLOBAL_PARAMETERS_TABLE
from antarest.study.dao.database.sql_utils import upsert_one

_TABLE = RESERVES_GLOBAL_PARAMETERS_TABLE


def _convert_row_to_model(row: Any) -> ReservesGlobalParameters:
    return ReservesGlobalParameters(
        reference_activation_duration_up=row.reference_activation_duration_up,
        energy_activation_ratio_up=row.energy_activation_ratio_up,
        reference_activation_duration_down=row.reference_activation_duration_down,
        energy_activation_ratio_down=row.energy_activation_ratio_down,
    )


class DatabaseReservesGlobalParametersDao(ReservesGlobalParametersDao):
    """Database implementation of ReservesGlobalParametersDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        return self._study_id

    def get_session(self) -> Session:
        return self._db_session

    @override
    def get_reserves_global_parameters(self, area_id: str) -> ReservesGlobalParameters:
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(_TABLE).where((_TABLE.c.study_id == study_id) & (_TABLE.c.area_id == area_id))
        row = session.execute(stmt).fetchone()
        if not row:
            return ReservesGlobalParameters()
        return _convert_row_to_model(row)

    @override
    def save_reserves_global_parameters(self, area_id: str, params: ReservesGlobalParameters) -> None:
        session = self.get_session()
        values = {
            "study_id": self.get_study_id(),
            "area_id": area_id,
            "reference_activation_duration_up": params.reference_activation_duration_up,
            "energy_activation_ratio_up": params.energy_activation_ratio_up,
            "reference_activation_duration_down": params.reference_activation_duration_down,
            "energy_activation_ratio_down": params.energy_activation_ratio_down,
        }
        upsert_one(session, _TABLE, values)
        session.commit()
