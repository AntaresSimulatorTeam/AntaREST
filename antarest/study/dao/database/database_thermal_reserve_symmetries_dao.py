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
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetry, merge_symmetries
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.thermal_reserve_symmetries_dao import ThermalReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.database.models.thermal_reserve_symmetries import THERMAL_RESERVE_SYMMETRIES_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


_TABLE = THERMAL_RESERVE_SYMMETRIES_TABLE


def _convert_row_to_model(row: Row[Any]) -> list[ReserveSymmetry]:
    symmetries: list[ReserveSymmetry] = json.loads(row.symmetries)
    return merge_symmetries(symmetries)


def _convert_model_to_row(
    study_id: str, area_id: str, thermal_id: str, reserve_id: str, certification: ThermalReserveCertification
) -> dict[str, Any]:
    values = certification.model_dump()
    values["reserve_id"] = reserve_id
    values["study_id"] = study_id
    values["area_id"] = area_id
    values["thermal_id"] = thermal_id
    return values


class DatabaseThermalReserveSymmetriesDao(ThermalReserveSymmetriesDao):
    """Database implementation of ThermalReserveSymmetriesDao."""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveSymmetriesMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, list[ReserveSymmetry]]:
        stmt = select(_TABLE).where((_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        result = {}
        for row in rows:
            result[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def set_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        raise NotImplementedError()
