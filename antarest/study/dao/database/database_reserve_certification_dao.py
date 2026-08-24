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

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from typing_extensions import override

from antarest.core.exceptions import (
    ReserveDefinitionsNotFound,
    STStoragesNotFound,
    ThermalClustersNotFound,
)
from antarest.study.business.model.reserve_certification_model import (
    ReserveCertification,
    StorageId,
    StorageReserveCertification,
    StorageReserveCertificationMapping,
    ThermalReserveCertification,
    ThermalReserveCertificationMapping,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.dao.api.reserve_certification_dao import ReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId
from antarest.study.dao.database.common import ReserveObjectType, validate_areas_exist
from antarest.study.dao.database.dao_context import DatabaseDaoBase


class DatabaseReserveCertificationDao(ReserveCertificationDao, DatabaseDaoBase):
    """Database implementation of ReserveCertificationDao."""

    @override
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        reserve_type = ReserveObjectType.THERMAL
        table = reserve_type.db_certification_table()
        stmt = select(table).where(table.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: dict[AreaId, ThermalReserveCertificationMapping] = {}
        for row in rows:
            certification = ThermalReserveCertification.model_validate(reserve_type.convert_row_to_mapping(row))
            result.setdefault(row.area_id, {}).setdefault(row.reserve_id, {})[row.thermal_id] = certification
        return result

    @override
    def get_thermal_reserve_certifications(self, area_id: AreaId) -> ThermalReserveCertificationMapping:
        reserve_type = ReserveObjectType.THERMAL
        table = reserve_type.db_certification_table()
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveCertificationMapping = {}
        for row in rows:
            certification = ThermalReserveCertification.model_validate(reserve_type.convert_row_to_mapping(row))
            result.setdefault(row.reserve_id, {})[row.thermal_id] = certification
        return result

    @override
    def save_thermal_reserve_certifications(
        self, new_certifications: dict[AreaId, ThermalReserveCertificationMapping]
    ) -> None:
        if not new_certifications:
            return

        old_certifications = self.get_all_thermal_reserve_certifications()

        try:
            self._save_certifications(ReserveObjectType.THERMAL, old_certifications, new_certifications)
        except IntegrityError as e:
            self._db_session.rollback()
            self._raise_the_right_thermal_reserve_exception(new_certifications, exc=e)
        self._db_session.commit()

    @override
    def get_all_st_storage_reserve_certifications(self) -> dict[AreaId, StorageReserveCertificationMapping]:
        reserve_type = ReserveObjectType.ST_STORAGE
        table = reserve_type.db_certification_table()
        stmt = select(table).where(table.c.study_data_id == self._study_data_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: dict[AreaId, StorageReserveCertificationMapping] = {}
        for row in rows:
            certification = StorageReserveCertification.model_validate(reserve_type.convert_row_to_mapping(row))
            result.setdefault(row.area_id, {}).setdefault(row.reserve_id, {})[row.st_storage_id] = certification
        return result

    @override
    def get_st_storage_reserve_certifications(self, area_id: AreaId) -> StorageReserveCertificationMapping:
        reserve_type = ReserveObjectType.ST_STORAGE
        table = reserve_type.db_certification_table()
        stmt = select(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        result: StorageReserveCertificationMapping = {}
        for row in rows:
            certification = StorageReserveCertification.model_validate(reserve_type.convert_row_to_mapping(row))
            result.setdefault(row.reserve_id, {})[row.st_storage_id] = certification
        return result

    @override
    def save_st_storage_reserve_certifications(
        self, new_certifications: dict[AreaId, StorageReserveCertificationMapping]
    ) -> None:
        old_certifications = self.get_all_st_storage_reserve_certifications()

        try:
            self._save_certifications(ReserveObjectType.ST_STORAGE, old_certifications, new_certifications)
        except IntegrityError as e:
            self._db_session.rollback()
            self._raise_the_right_st_storage_reserve_exception(new_certifications, exc=e)

        self._db_session.commit()

    def _save_certifications(
        self,
        reserve_type: ReserveObjectType,
        old_certifications: dict[AreaId, dict[ReserveDefinitionId, dict[str, Any]]],
        new_certifications: dict[AreaId, dict[ReserveDefinitionId, dict[str, Any]]],
    ) -> None:
        values = []
        for area_id, reserves_dict in new_certifications.items():
            for reserve_id, value in reserves_dict.items():
                for object_id, certification in value.items():
                    values.append(
                        reserve_type.convert_certification_to_row(
                            self._study_data_id, area_id, object_id, reserve_id, certification
                        )
                    )
        table = reserve_type.db_certification_table()
        area_ids = set(new_certifications)
        stmt = delete(table).where((table.c.study_data_id == self._study_data_id) & (table.c.area_id.in_(area_ids)))
        self._db_session.execute(stmt)
        if values:
            self._db_session.execute(insert(table), values)

        # Clean orphan symmetries
        for area_id, reserves_dict in old_certifications.items():
            missing_reserves: dict[str, set[ReserveDefinitionId]] = {}
            for reserve_id, v in old_certifications[area_id].items():
                for object_id in v:
                    if object_id not in new_certifications.get(area_id, {}).get(reserve_id, {}):
                        missing_reserves.setdefault(object_id, set()).add(reserve_id)
            if missing_reserves:
                if reserve_type == ReserveObjectType.THERMAL:
                    self.get_impl().delete_orphan_thermal_symmetries(area_id, missing_reserves)
                else:
                    self.get_impl().delete_orphan_st_storage_symmetries(area_id, missing_reserves)

    def _raise_the_right_thermal_reserve_exception(
        self,
        data: dict[AreaId, ThermalReserveCertificationMapping],
        exc: IntegrityError | None = None,
    ) -> NoReturn:
        validate_areas_exist(self._db_session, self._study_data_id, set(data))
        self._raise_exception_if_missing_reserve(data)

        # Checks if some thermals are missing
        all_existing_thermals = self.get_impl().get_all_thermals()
        invalid_thermal_dict: dict[AreaId, set[ThermalId]] = {}
        for area_id, reserves_dict in data.items():
            for thermal_ids in reserves_dict.values():
                if invalid_thermals := set(thermal_ids) - set(all_existing_thermals.get(area_id, [])):
                    invalid_thermal_dict.setdefault(area_id, set())
                    invalid_thermal_dict[area_id] |= invalid_thermals

        if invalid_thermal_dict:
            raise ThermalClustersNotFound(invalid_thermal_dict) from exc

        # All objects exist. It means that the DB table does not contain the information.
        raise ValueError("One of the thermal reserve certification table is not filled as it should") from exc

    def _raise_the_right_st_storage_reserve_exception(
        self,
        data: dict[AreaId, StorageReserveCertificationMapping],
        exc: IntegrityError | None = None,
    ) -> NoReturn:
        validate_areas_exist(self._db_session, self._study_data_id, set(data))
        self._raise_exception_if_missing_reserve(data)

        all_existing_st_storage = self.get_impl().get_all_st_storages()
        invalid_st_storage_dict: dict[AreaId, set[StorageId]] = {}
        for area_id, reserves_dict in data.items():
            for st_storage_ids in reserves_dict.values():
                if invalid_st_storage := set(st_storage_ids) - set(all_existing_st_storage.get(area_id, [])):
                    invalid_st_storage_dict.setdefault(area_id, set())
                    invalid_st_storage_dict[area_id] |= invalid_st_storage

        if invalid_st_storage_dict:
            raise STStoragesNotFound(invalid_st_storage_dict) from exc

        # All objects exist. It means that the DB table does not contain the information.
        raise ValueError(
            "One of the short-term storage reserve certification table is not filled as it should"
        ) from exc

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
