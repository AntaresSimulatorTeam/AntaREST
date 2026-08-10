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
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import Row, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound, ThermalReserveCertificationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import check_thermal_symmetries_are_certified
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.database.models.thermal_reserve_symmetries import THERMAL_RESERVE_SYMMETRIES_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


_THERMAL_TABLE = THERMAL_RESERVE_SYMMETRIES_TABLE


def _convert_row_to_model(row: Row[Any]) -> ReserveSymmetries:
    return cast(ReserveSymmetries, json.loads(row.symmetries))


def _convert_model_to_row(
    study_id: str, area_id: str, thermal_id: str, symmetries: ReserveSymmetries
) -> dict[str, Any]:
    values = {"study_id": study_id, "area_id": area_id, "thermal_id": thermal_id, "symmetries": json.dumps(symmetries)}
    return values


def _checks_foreign_key_integrity(
    new_data: ThermalReserveSymmetriesMapping, reserve_ids: dict[AreaId, list[ReserveDefinitionId]]
) -> None:
    """
    There is no foreign key constraint between symmetries and reserve ids but they are linked.
    So we have to check the data integrity manually.
    """
    for area_id, value in new_data.items():
        if area_id not in reserve_ids:
            raise AreaNotFound(area_id)
        for symmetries in value.values():
            for symmetry in symmetries:
                for reserve_id in symmetry:
                    if reserve_id not in reserve_ids[area_id]:
                        raise ReserveDefinitionNotFound(area_id, reserve_id)


class DatabaseReserveSymmetriesDao(ReserveSymmetriesDao):
    """Database implementation of ReserveSymmetriesDao."""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        stmt = select(_THERMAL_TABLE).where(_THERMAL_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveSymmetriesMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        stmt = select(_THERMAL_TABLE).where(
            (_THERMAL_TABLE.c.study_id == self._study_id) & (_THERMAL_TABLE.c.area_id == area_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        result = {}
        for row in rows:
            result[row.thermal_id] = _convert_row_to_model(row)
        return result

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        # Check foreign key integrity
        existing_reserve_definitions = self.get_impl().get_all_reserve_definitions()
        existing_reserve_ids = {}
        for area_id, value in existing_reserve_definitions.items():
            existing_reserve_ids[area_id] = list(value)
        _checks_foreign_key_integrity(data, existing_reserve_ids)

        # Verify that the thermals are certified on the reserves they are symmetric on
        for area_id, thermal_dict in data.items():
            certifications = self.get_impl().get_thermal_reserve_certifications(area_id)
            try:
                check_thermal_symmetries_are_certified(area_id, thermal_dict, certifications)
            except ThermalReserveCertificationNotFound:
                # A missing certification is ambiguous: the thermal may simply not exist.
                existing_ids = {thermal.id for thermal in self.get_impl().get_all_thermals_for_area(area_id)}
                if unknown_ids := [t_id for t_id in thermal_dict if t_id not in existing_ids]:
                    self.get_impl().raise_the_right_thermal_exception({area_id: unknown_ids})
                raise

        # Save the new values
        values = []
        for area_id, thermal_dict in data.items():
            for thermal_id, symmetries in thermal_dict.items():
                if symmetries == [[]]:
                    continue
                values.append(_convert_model_to_row(self._study_id, area_id, thermal_id, symmetries))
        try:
            # First, clean the DB
            area_ids = set(data)
            stmt = delete(_THERMAL_TABLE).where(
                (_THERMAL_TABLE.c.study_id == self._study_id) & (_THERMAL_TABLE.c.area_id.in_(area_ids))
            )
            self._db_session.execute(stmt)
            # Then, insert the new values
            if values:
                self._db_session.execute(insert(_THERMAL_TABLE), values)
        except IntegrityError as e:
            thermals = {area_id: list(thermal_dict) for area_id, thermal_dict in data.items()}
            self.get_impl().raise_the_right_thermal_exception(thermals, exc=e)
        self._db_session.commit()
