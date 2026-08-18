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
from typing import Any, cast

from sqlalchemy import Row, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import (
    ReserveDefinitionNotFound,
    ThermalReserveCertificationNotFound,
    ThermalReserveCertificationsNotFound,
)
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.database.common import validate_area_exists
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.thermal_reserve_symmetries import THERMAL_RESERVE_SYMMETRIES_TABLE

_THERMAL_TABLE = THERMAL_RESERVE_SYMMETRIES_TABLE


def _convert_row_to_model(row: Row[Any]) -> ReserveSymmetries:
    return cast(ReserveSymmetries, json.loads(row.symmetries))


def _convert_model_to_row(
    study_data_id: int, area_id: str, thermal_id: str, symmetries: ReserveSymmetries
) -> dict[str, Any]:
    values = {
        "study_data_id": study_data_id,
        "area_id": area_id,
        "thermal_id": thermal_id,
        "symmetries": json.dumps(symmetries),
    }
    return values


class DatabaseReserveSymmetriesDao(ReserveSymmetriesDao, DatabaseDaoBase):
    """Database implementation of ReserveSymmetriesDao."""

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        stmt = select(_THERMAL_TABLE).where(_THERMAL_TABLE.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveSymmetriesMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        stmt = select(_THERMAL_TABLE).where(
            (_THERMAL_TABLE.c.study_data_id == self._study_data_id) & (_THERMAL_TABLE.c.area_id == area_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        result = {}
        for row in rows:
            result[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        # Check foreign key integrity
        existing_certifications = self.get_impl().get_all_thermal_reserve_certifications()

        for area_id, value in data.items():
            if area_id not in existing_certifications:
                # Means that either the area does not exist, or the area does not contain any thermal certification.
                validate_area_exists(self._db_session, self._study_data_id, area_id)
                raise ThermalReserveCertificationsNotFound(area_id)

            for thermal_id, symmetries in value.items():
                for symmetry in symmetries:
                    for reserve_id in symmetry:
                        if reserve_id not in existing_certifications[area_id]:
                            raise ReserveDefinitionNotFound(area_id, reserve_id)
                        if thermal_id not in existing_certifications[area_id][reserve_id]:
                            raise ThermalReserveCertificationNotFound(area_id, thermal_id, {reserve_id})

        # Save the new values
        values = []
        for area_id, thermal_dict in data.items():
            for thermal_id, symmetries in thermal_dict.items():
                if symmetries == [[]]:
                    continue
                values.append(_convert_model_to_row(self._study_data_id, area_id, thermal_id, symmetries))
        try:
            # First, clean the DB
            area_ids = set(data)
            stmt = delete(_THERMAL_TABLE).where(
                (_THERMAL_TABLE.c.study_data_id == self._study_data_id) & (_THERMAL_TABLE.c.area_id.in_(area_ids))
            )
            self._db_session.execute(stmt)
            # Then, insert the new values
            if values:
                self._db_session.execute(insert(_THERMAL_TABLE), values)
        except IntegrityError as e:
            self._db_session.rollback()
            thermals = {area_id: list(thermal_dict) for area_id, thermal_dict in data.items()}
            self.get_impl().raise_the_right_thermal_exception(thermals, exc=e)
        self._db_session.commit()
