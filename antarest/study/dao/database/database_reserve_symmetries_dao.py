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
from typing import Sequence

from sqlalchemy import Row, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound, ThermalReserveCertificationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.api.common import check_thermal_symmetries_are_certified
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

_THERMAL_TABLE = THERMAL_RESERVE_SYMMETRIES_TABLE
_ST_STORAGE_TABLE = ST_STORAGE_RESERVE_SYMMETRIES_TABLE


def _convert_row_to_model(row: Row[Any]) -> ReserveSymmetries:
    return cast(ReserveSymmetries, json.loads(row.symmetries))


def _convert_thermal_model_to_row(
    study_data_id: int, area_id: str, thermal_id: str, symmetries: ReserveSymmetries
) -> dict[str, Any]:
    values = {
        "study_data_id": study_data_id,
        "area_id": area_id,
        "thermal_id": thermal_id,
        "symmetries": json.dumps(symmetries),
    }
    return values


def _convert_st_storage_model_to_row(
    study_id: str, area_id: str, st_storage_id: str, symmetries: ReserveSymmetries
) -> dict[str, Any]:
    values = {
        "study_id": study_id,
        "area_id": area_id,
        "st_storage_id": st_storage_id,
        "symmetries": json.dumps(symmetries),
    }
    return values


def _convert_all_rows_to_model(rows: Sequence[Row[tuple[Any]]], id_field_name: str) -> dict[Any, Any]:
    result = {}
    for row in rows:
        result[row._mapping[id_field_name]] = _convert_row_to_model(row)
    return result


def _convert_all_rows_to_dict_of_models(
    rows: Sequence[Row[tuple[Any]]], id_field_name: str
) -> dict[str, dict[str, list[list[ReserveDefinitionId]]]]:
    result: ReserveSymmetriesMapping = {}
    for row in rows:
        result.setdefault(row.area_id, {})[row._mapping[id_field_name]] = _convert_row_to_model(row)
    return result


def _checks_foreign_key_integrity(
    new_data: ReserveSymmetriesMapping, reserve_ids: dict[AreaId, list[ReserveDefinitionId]]
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


class DatabaseReserveSymmetriesDao(ReserveSymmetriesDao, DatabaseDaoBase):
    """Database implementation of ReserveSymmetriesDao."""

    @override
    def get_all_thermal_reserve_symmetries(self) -> ThermalReserveSymmetriesMapping:
        rows = self._get_all_area_assets_matching_study_id(_THERMAL_TABLE)
        return _convert_all_rows_to_dict_of_models(rows, "thermal_id")

    def _get_all_area_assets_matching_study_id(self, table: Table) -> Sequence[Row[tuple[Any]]]:
        stmt = select(table).where(table.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        return rows

    @override
    def get_thermal_reserve_symmetries(self, area_id: AreaId) -> dict[ThermalId, ReserveSymmetries]:
        rows = self._get_all_area_assets_matching_area(area_id, _THERMAL_TABLE)
        return _convert_all_rows_to_model(rows, "thermal_id")

    def _get_all_area_assets_matching_area(self, area_id: str, table: Table) -> Sequence[Row[tuple[Any]]]:
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        return rows

    @override
    def save_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        self._check_foreign_key_integrity(data)

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
                values.append(_convert_thermal_model_to_row(self._study_data_id, area_id, thermal_id, symmetries))
        try:
            self.__clean_db(_THERMAL_TABLE, data)
            self.__insert_data_to_table(_THERMAL_TABLE, values)
        except IntegrityError as e:
            self._db_session.rollback()
            thermals = {area_id: list(thermal_dict) for area_id, thermal_dict in data.items()}
            self.get_impl().raise_the_right_thermal_exception(thermals, exc=e)
        self._db_session.commit()

    @override
    def get_all_st_storage_reserve_symmetries(self) -> STStorageReserveSymmetriesMapping:
        rows = self._get_all_area_assets_matching_study_id(_ST_STORAGE_TABLE)
        return _convert_all_rows_to_dict_of_models(rows, "st_storage_id")

    @override
    def get_st_storage_reserve_symmetries(self, area_id: AreaId) -> dict[StStorageId, ReserveSymmetries]:
        rows = self._get_all_area_assets_matching_area(area_id, _ST_STORAGE_TABLE)
        return _convert_all_rows_to_model(rows, "st_storage_id")

    @override
    def save_st_storage_reserve_symmetries(self, data: STStorageReserveSymmetriesMapping) -> None:
        self._check_foreign_key_integrity(data)

        # Save the new values
        values = []
        for area_id, st_storage_dict in data.items():
            for st_storage_id, symmetries in st_storage_dict.items():
                if symmetries == [[]]:
                    continue
                values.append(_convert_st_storage_model_to_row(self._study_id, area_id, st_storage_id, symmetries))
        try:
            self.__clean_db(_ST_STORAGE_TABLE, data)
            self.__insert_data_to_table(_ST_STORAGE_TABLE, values)
        except IntegrityError as e:
            st_storages = {area_id: list(st_storage_dict) for area_id, st_storage_dict in data.items()}
            self.get_impl().raise_the_right_storage_exception(st_storages, exc=e)
        self._db_session.commit()

    def __clean_db(self, table: Table, data: dict[str, dict[str, list[list[ReserveDefinitionId]]]]) -> None:
        area_ids = set(data)
        stmt = delete(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id.in_(area_ids)))
        self._db_session.execute(stmt)

    def __insert_data_to_table(self, table: Table, values: list[Any]) -> None:
        if values:
            self._db_session.execute(insert(table), values)

    def _check_foreign_key_integrity(self, data: dict[str, dict[str, list[list[ReserveDefinitionId]]]]) -> None:
        existing_reserve_definitions = self.get_impl().get_all_reserve_definitions()
        existing_reserve_ids = {}
        for area_id, value in existing_reserve_definitions.items():
            existing_reserve_ids[area_id] = list(value)
        _checks_foreign_key_integrity(data, existing_reserve_ids)
