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
from enum import StrEnum
from typing import Any, Sequence, cast

from sqlalchemy import Row, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import check_st_storage_symmetries_integrity, check_thermal_symmetries_integrity
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    ReserveSymmetriesMapping,
    StStorageId,
    STStorageReserveSymmetriesMapping,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.st_storage_reserve_symmetries import ST_STORAGE_RESERVE_SYMMETRIES_TABLE
from antarest.study.dao.database.models.thermal_reserve_symmetries import THERMAL_RESERVE_SYMMETRIES_TABLE


def _convert_row_to_model(row: Row[Any]) -> ReserveSymmetries:
    return cast(ReserveSymmetries, json.loads(row.symmetries))


class SymmetryType(StrEnum):
    THERMAL = "thermal"
    ST_STORAGE = "st_storage"

    def _db_key(self) -> str:
        if self == SymmetryType.THERMAL:
            return "thermal_id"
        else:
            return "st_storage_id"

    def db_table(self) -> Table:
        if self == SymmetryType.THERMAL:
            return THERMAL_RESERVE_SYMMETRIES_TABLE
        else:
            return ST_STORAGE_RESERVE_SYMMETRIES_TABLE

    def convert_to_row(
        self, study_data_id: int, area_id: str, object_id: str, symmetries: ReserveSymmetries
    ) -> dict[str, Any]:
        return {
            "study_data_id": study_data_id,
            "area_id": area_id,
            "symmetries": json.dumps(symmetries),
            self._db_key(): object_id,
        }

    def convert_all_rows_to_model(self, rows: Sequence[Row[Any]]) -> dict[str, ReserveSymmetries]:
        result = {}
        for row in rows:
            row_as_dict = get_row_representation_as_dict(row)
            result[row_as_dict[self._db_key()]] = _convert_row_to_model(row)
        return result

    def convert_all_rows_to_dict_of_models(self, rows: Sequence[Row[Any]]) -> ReserveSymmetriesMapping:
        result: ReserveSymmetriesMapping = {}
        for row in rows:
            row_as_dict = get_row_representation_as_dict(row)
            result.setdefault(row.area_id, {})[row_as_dict[self._db_key()]] = _convert_row_to_model(row)
        return result


class DatabaseReserveSymmetriesDao(ReserveSymmetriesDao, DatabaseDaoBase):
    """Database implementation of ReserveSymmetriesDao."""

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        return self._get_all_symmetries(SymmetryType.THERMAL)

    @override
    def get_all_st_storage_reserve_symmetries(self) -> STStorageReserveSymmetriesMapping:
        return self._get_all_symmetries(SymmetryType.ST_STORAGE)

    def _get_all_symmetries(self, symmetry_type: SymmetryType) -> ReserveSymmetriesMapping:
        table = symmetry_type.db_table()
        stmt = select(table).where(table.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        return symmetry_type.convert_all_rows_to_dict_of_models(rows)

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        return self._get_all_symmetries_for_area(area_id, SymmetryType.THERMAL)

    @override
    def get_st_storage_reserve_symmetries(self, area_id: AreaId) -> dict[StStorageId, ReserveSymmetries]:
        return self._get_all_symmetries_for_area(area_id, SymmetryType.ST_STORAGE)

    def _get_all_symmetries_for_area(self, area_id: str, symmetry_type: SymmetryType) -> dict[str, ReserveSymmetries]:
        table = symmetry_type.db_table()
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        return symmetry_type.convert_all_rows_to_model(rows)

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        # Check foreign keys integrity
        check_thermal_symmetries_integrity(self.get_impl(), data)

        # Save the new values
        try:
            self._save_reserve_symmetries(data, SymmetryType.THERMAL)
        except IntegrityError as e:
            self._db_session.rollback()
            thermals = {area_id: list(thermal_dict) for area_id, thermal_dict in data.items()}
            self.get_impl().raise_the_right_thermal_exception(thermals, exc=e)
        self._db_session.commit()

    @override
    def save_st_storage_reserve_symmetries(self, data: STStorageReserveSymmetriesMapping) -> None:
        # Check foreign keys integrity
        check_st_storage_symmetries_integrity(self.get_impl(), data)

        # Save the new values
        try:
            self._save_reserve_symmetries(data, SymmetryType.ST_STORAGE)
        except IntegrityError as e:
            self._db_session.rollback()
            st_storages = {area_id: list(st_storage_dict) for area_id, st_storage_dict in data.items()}
            self.get_impl().raise_the_right_storage_exception(st_storages, exc=e)
        self._db_session.commit()

    def _save_reserve_symmetries(self, data: ReserveSymmetriesMapping, symmetry_type: SymmetryType) -> None:
        values = []
        for area_id, value in data.items():
            for object_id, symmetries in value.items():
                if symmetries == [[]]:
                    continue
                values.append(symmetry_type.convert_to_row(self._study_data_id, area_id, object_id, symmetries))

        table = symmetry_type.db_table()
        stmt = delete(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id.in_(set(data))))
        self._db_session.execute(stmt)
        if values:
            self._db_session.execute(insert(table), values)
