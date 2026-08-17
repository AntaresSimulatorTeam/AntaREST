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
from collections.abc import Mapping
from typing import Any, NoReturn

from sqlalchemy import Row, Select, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveDefinitionsNotFound,
    STStoragesNotFound,
    ThermalClustersNotFound,
)
from antarest.dbmodel import get_row_representation_as_dict
from antarest.study.business.model.reserve_certification_model import (
    ReserveCertification,
    StorageReserveCertification,
    StorageReserveCertificationMapping,
    ThermalReserveCertification,
    ThermalReserveCertificationMapping,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.dao.api.reserve_certification_dao import ReserveCertificationDao
from antarest.study.dao.common import AreaId
from antarest.study.dao.database.dao_context import DatabaseDaoBase
from antarest.study.dao.database.models.st_storage_reserve_certification import ST_STORAGE_RESERVE_CERTIFICATION_TABLE
from antarest.study.dao.database.models.thermal_reserve_certification import THERMAL_RESERVE_CERTIFICATION_TABLE

_THERMAL_TABLE = THERMAL_RESERVE_CERTIFICATION_TABLE
_ST_STORAGE_TABLE = ST_STORAGE_RESERVE_CERTIFICATION_TABLE


def _convert_thermal_row_to_model(row: Row[Any]) -> ThermalReserveCertification:
    data = get_row_representation_as_dict(row)
    for key in ("study_data_id", "area_id", "thermal_id", "reserve_id"):
        del data[key]
    return ThermalReserveCertification.model_validate(data)


def _convert_thermal_model_to_row(
    study_data_id: str, area_id: str, thermal_id: str, reserve_id: str, certification: ThermalReserveCertification
) -> dict[str, Any]:
    values = certification.model_dump()
    values["reserve_id"] = reserve_id
    values["study_data_id"] = study_data_id
    values["area_id"] = area_id
    values["thermal_id"] = thermal_id
    return values


def _convert_st_storage_row_to_model(row: Row[Any]) -> StorageReserveCertification:
    data = get_row_representation_as_dict(row)
    for key in ("study_id", "area_id", "st_storage_id", "reserve_id"):
        del data[key]
    return StorageReserveCertification.model_validate(data)


def _convert_st_storage_model_to_row(
    study_id: str, area_id: str, storage_id: str, reserve_id: str, certification: StorageReserveCertification
) -> dict[str, Any]:
    values = certification.model_dump()
    values["study_id"] = study_id
    values["area_id"] = area_id
    values["st_storage_id"] = storage_id
    values["reserve_id"] = reserve_id
    return values


class DatabaseReserveCertificationDao(ReserveCertificationDao, DatabaseDaoBase):
    """Database implementation of ReserveCertificationDao."""

    def _select_one(self, area_id: str, thermal_id: str, reserve_id: str) -> Select[Any]:
        return select(_THERMAL_TABLE).where(
            (_THERMAL_TABLE.c.study_data_id == self._study_data_id)
            & (_THERMAL_TABLE.c.area_id == area_id)
            & (_THERMAL_TABLE.c.thermal_id == thermal_id)
            & (_THERMAL_TABLE.c.reserve_id == reserve_id)
        )

    @override
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        stmt = select(_THERMAL_TABLE).where(_THERMAL_TABLE.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: dict[AreaId, ThermalReserveCertificationMapping] = {}
        for row in rows:
            certification = _convert_thermal_row_to_model(row)
            result.setdefault(row.area_id, {}).setdefault(row.reserve_id, {})[row.thermal_id] = certification
        return result

    @override
    def get_thermal_reserve_certifications(self, area_id: AreaId) -> ThermalReserveCertificationMapping:
        stmt = select(_THERMAL_TABLE).where(
            (_THERMAL_TABLE.c.study_data_id == self._study_data_id) & (_THERMAL_TABLE.c.area_id == area_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveCertificationMapping = {}
        for row in rows:
            result.setdefault(row.reserve_id, {})[row.thermal_id] = _convert_thermal_row_to_model(row)
        return result

    @override
    def save_thermal_reserve_certifications(
        self, new_certifications: dict[AreaId, ThermalReserveCertificationMapping]
    ) -> None:
        if not new_certifications:
            return
        values = []
        for area_id, reserves_dict in new_certifications.items():
            for reserve_id, thermal_dict in reserves_dict.items():
                for thermal_id, certification in thermal_dict.items():
                    values.append(
                        _convert_thermal_model_to_row(self._study_data_id, area_id, thermal_id, reserve_id, certification)
                    )
        try:
            self._clean_db(_THERMAL_TABLE, new_certifications)
            self._insert_data_to_table(_THERMAL_TABLE, values)
        except IntegrityError as e:
            self._raise_the_right_thermal_reserve_exception(new_certifications, exc=e)
        self._db_session.commit()

    def _raise_the_right_thermal_reserve_exception(
        self,
        data: dict[AreaId, ThermalReserveCertificationMapping],
        exc: IntegrityError | None = None,
    ) -> NoReturn:
        self._raise_exception_if_missing_area(data)
        self._raise_exception_if_missing_reserve(data)

        # Checks if some thermals are missing
        all_existing_thermals = self.get_impl().get_all_thermals()
        invalid_thermal_dict = {}
        for area_id, reserves_dict in data.items():
            for thermal_ids in reserves_dict.values():
                if invalid_thermals := set(thermal_ids) - set(all_existing_thermals.get(area_id, [])):
                    invalid_thermal_dict[area_id] = invalid_thermals

        if invalid_thermal_dict:
            raise ThermalClustersNotFound(invalid_thermal_dict) from exc

        # All objects exist. It means that the DB table does not contain the information.
        raise ValueError("One of the thermal reserve certification table is not filled as it should") from exc

    @override
    def get_all_st_storage_reserve_certifications(self) -> dict[AreaId, StorageReserveCertificationMapping]:
        stmt = select(_ST_STORAGE_TABLE).where(_ST_STORAGE_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: dict[AreaId, StorageReserveCertificationMapping] = {}
        for row in rows:
            certification = _convert_st_storage_row_to_model(row)
            result.setdefault(row.area_id, {}).setdefault(row.reserve_id, {})[row.st_storage_id] = certification
        return result

    @override
    def get_st_storage_reserve_certifications(self, area_id: AreaId) -> StorageReserveCertificationMapping:
        stmt = select(_ST_STORAGE_TABLE).where(
            (_ST_STORAGE_TABLE.c.study_id == self._study_id) & (_ST_STORAGE_TABLE.c.area_id == area_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        result: StorageReserveCertificationMapping = {}
        for row in rows:
            result.setdefault(row.reserve_id, {})[row.st_storage_id] = _convert_st_storage_row_to_model(row)
        return result

    @override
    def save_st_storage_reserve_certifications(
        self, new_certifications: dict[AreaId, StorageReserveCertificationMapping]
    ) -> None:
        if not new_certifications:
            return
        values = self._convert_st_storages_models_to_rows(new_certifications)
        try:
            self._clean_db(_ST_STORAGE_TABLE, new_certifications)
            self._insert_data_to_table(_ST_STORAGE_TABLE, values)
        except IntegrityError as e:
            self._raise_the_right_st_storage_reserve_exception(new_certifications, exc=e)
        self._db_session.commit()

    def _convert_st_storages_models_to_rows(
        self, data: dict[str, dict[ReserveDefinitionId, dict[str, StorageReserveCertification]]]
    ) -> list[Any]:
        values = []
        for area_id, reserves_dict in data.items():
            for reserve_id, storage_dict in reserves_dict.items():
                for storage_id, certification in storage_dict.items():
                    values.append(
                        _convert_st_storage_model_to_row(self._study_id, area_id, storage_id, reserve_id, certification)
                    )
        return values

    def _clean_db(
        self, table: Table, data: Mapping[str, Mapping[ReserveDefinitionId, Mapping[str, ReserveCertification]]]
    ) -> None:
        area_ids = set(data)
        stmt = delete(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id.in_(area_ids)))
        self._db_session.execute(stmt)

    def _insert_data_to_table(self, table: Table, values: list[Any]) -> None:
        if values:
            self._db_session.execute(insert(table), values)

    def _raise_the_right_st_storage_reserve_exception(
        self,
        data: dict[AreaId, StorageReserveCertificationMapping],
        exc: IntegrityError | None = None,
    ) -> NoReturn:
        self._raise_exception_if_missing_area(data)
        self._raise_exception_if_missing_reserve(data)

        all_existing_st_storage = self.get_impl().get_all_st_storages()
        invalid_st_storage_dict = {}
        for area_id, reserves_dict in data.items():
            for st_storage_ids in reserves_dict.values():
                if invalid_st_storage := set(st_storage_ids) - set(all_existing_st_storage.get(area_id, [])):
                    invalid_st_storage_dict[area_id] = invalid_st_storage

        if invalid_st_storage_dict:
            raise STStoragesNotFound(invalid_st_storage_dict) from exc

        # All objects exist. It means that the DB table does not contain the information.
        raise ValueError(
            "One of the short-term storage reserve certification table is not filled as it should"
        ) from exc

    def _raise_exception_if_missing_area(
        self, data: Mapping[str, Mapping[ReserveDefinitionId, Mapping[str, ReserveCertification]]]
    ) -> None:
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

    def _raise_exception_if_missing_reserve(
        self, data: Mapping[str, Mapping[ReserveDefinitionId, Mapping[str, ReserveCertification]]]
    ) -> None:
        all_existing_reserves = self.get_impl().get_all_reserve_definitions()
        invalid_reserves_dict = {}
        for area_id, reserves_dict in data.items():
            if invalid_reserves := set(reserves_dict) - set(all_existing_reserves.get(area_id, {})):
                invalid_reserves_dict[area_id] = invalid_reserves

        if invalid_reserves_dict:
            raise ReserveDefinitionsNotFound(invalid_reserves_dict)  # type: ignore
