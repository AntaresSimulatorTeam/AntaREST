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
from typing import Any

from sqlalchemy import Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import (
    check_hydro_symmetries_integrity,
    check_st_storage_symmetries_integrity,
    check_thermal_symmetries_integrity,
)
from antarest.study.dao.api.reserve_symmetries_dao import ReserveSymmetriesDao
from antarest.study.dao.common import (
    AreaId,
    HydroReserveSymmetriesMapping,
    ReserveSymmetriesMapping,
    StStorageId,
    STStorageReserveSymmetriesMapping,
    ThermalId,
    ThermalReserveSymmetriesMapping,
)
from antarest.study.dao.database.common import ReserveObjectType, convert_row_to_symmetries, validate_areas_exist
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.hydro_reserve_symmetries import HYDRO_RESERVE_SYMMETRIES_TABLE


class DatabaseReserveSymmetriesDao(ReserveSymmetriesDao, DatabaseDaoBase):
    """Database implementation of ReserveSymmetriesDao."""

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        return self._get_all_symmetries(ReserveObjectType.THERMAL)

    @override
    def get_all_st_storage_reserve_symmetries(self) -> STStorageReserveSymmetriesMapping:
        return self._get_all_symmetries(ReserveObjectType.ST_STORAGE)

    def _get_all_symmetries(self, reserve_type: ReserveObjectType) -> ReserveSymmetriesMapping:
        table = reserve_type.db_symmetry_table()
        stmt = select(table).where(table.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        return reserve_type.convert_all_rows_to_dict_of_symmetries(rows)

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        return self._get_all_symmetries_for_area(area_id, ReserveObjectType.THERMAL)

    @override
    def get_st_storage_reserve_symmetries(self, area_id: AreaId) -> dict[StStorageId, ReserveSymmetries]:
        return self._get_all_symmetries_for_area(area_id, ReserveObjectType.ST_STORAGE)

    def _get_all_symmetries_for_area(
        self, area_id: str, reserve_type: ReserveObjectType
    ) -> dict[str, ReserveSymmetries]:
        table = reserve_type.db_symmetry_table()
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        return reserve_type.convert_all_rows_to_symmetries(rows)

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        reserve_type = ReserveObjectType.THERMAL
        values = self._build_symmetry_rows(data, reserve_type)

        if values:
            # Check foreign keys integrity for values to insert
            check_thermal_symmetries_integrity(self.get_impl(), data)

        # Save the new values
        try:
            self._save_reserve_symmetries(set(data), reserve_type.db_symmetry_table(), values)
        except IntegrityError as e:
            self._db_session.rollback()
            thermals = {area_id: list(thermal_dict) for area_id, thermal_dict in data.items()}
            self.get_impl().raise_the_right_thermal_exception(thermals, exc=e)
        self._db_session.commit()

    @override
    def save_st_storage_reserve_symmetries(self, data: STStorageReserveSymmetriesMapping) -> None:
        reserve_type = ReserveObjectType.ST_STORAGE
        values = self._build_symmetry_rows(data, reserve_type)

        if values:
            # Check foreign keys integrity for values to insert
            check_st_storage_symmetries_integrity(self.get_impl(), data)

        # Save the new values
        try:
            self._save_reserve_symmetries(set(data), reserve_type.db_symmetry_table(), values)
        except IntegrityError as e:
            self._db_session.rollback()
            st_storages = {area_id: list(st_storage_dict) for area_id, st_storage_dict in data.items()}
            self.get_impl().raise_the_right_storage_exception(st_storages, exc=e)
        self._db_session.commit()

    def _build_symmetry_rows(
        self, data: ReserveSymmetriesMapping, reserve_type: ReserveObjectType
    ) -> list[dict[str, Any]]:
        values = []
        for area_id, value in data.items():
            for object_id, symmetries in value.items():
                if not (any(symmetry for symmetry in symmetries)):
                    continue
                values.append(reserve_type.convert_symmetry_to_row(self._study_data_id, area_id, object_id, symmetries))
        return values

    def _save_reserve_symmetries(self, area_ids: set[str], table: Table, values: list[dict[str, Any]]) -> None:
        stmt = delete(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id.in_(area_ids)))
        self._db_session.execute(stmt)
        if values:
            self._db_session.execute(insert(table), values)

    @override
    def get_all_hydro_reserve_symmetries(self) -> HydroReserveSymmetriesMapping:
        table = HYDRO_RESERVE_SYMMETRIES_TABLE
        stmt = select(table).where(table.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        return {row.area_id: convert_row_to_symmetries(row) for row in rows}

    @override
    def get_hydro_reserve_symmetries(self, area_id: AreaId) -> ReserveSymmetries:
        table = HYDRO_RESERVE_SYMMETRIES_TABLE
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        row = self._db_session.execute(stmt).fetchone()
        return convert_row_to_symmetries(row) if row is not None else []

    @override
    def save_hydro_reserve_symmetries(self, data: HydroReserveSymmetriesMapping) -> None:
        values = []
        for area_id, symmetries in data.items():
            if not (any(symmetry for symmetry in symmetries)):
                continue
            values.append(
                {
                    "study_data_id": self._study_data_id,
                    "area_id": area_id,
                    "symmetries": json.dumps([symmetry for symmetry in symmetries if symmetry]),
                }
            )

        if values:
            # Check foreign keys integrity for values to insert
            check_hydro_symmetries_integrity(self.get_impl(), data)
        else:
            # We need this check to avoid performing a silent no-op
            # User should know when they send an invalid area
            validate_areas_exist(self._db_session, self._study_data_id, set(data))

        try:
            self._save_reserve_symmetries(set(data), HYDRO_RESERVE_SYMMETRIES_TABLE, values)
        except IntegrityError as e:
            self._db_session.rollback()
            validate_areas_exist(self._db_session, self._study_data_id, set(data))
            raise ValueError("The hydro reserve symmetries table is not filled as it should") from e
        self._db_session.commit()
