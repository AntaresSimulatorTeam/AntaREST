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
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, NoReturn

from sqlalchemy import CursorResult, Row, Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveDefinitionsNotFound,
    ThermalClustersNotFound,
    ThermalReserveCertificationNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.thermal_reserve_certification_dao import THERMAL_RESERVE_CERTIFICATION_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


_TABLE = THERMAL_RESERVE_CERTIFICATION_TABLE

def _convert_row_to_model(row: Row[Any]) -> ThermalReserveCertification:
    data = get_row_representation_as_dict(row)
    for key in ("study_id", "area_id", "thermal_id", "reserve_id"):
        del data[key]
    return ThermalReserveCertification.model_validate(data)

def _convert_model_to_row(
    study_id: str, area_id: str, thermal_id: str, reserve_id: str, certification: ThermalReserveCertification
) -> dict[str, Any]:
    values = certification.model_dump()
    values["reserve_id"] = reserve_id
    values["study_id"] = study_id
    values["area_id"] = area_id
    values["thermal_id"] = thermal_id
    return values

class DatabaseThermalReserveCertificationDao(ThermalReserveCertificationDao):
    """Database implementation of ThermalReserveCertificationDao."""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def _select_one(self, area_id: str, thermal_id: str, reserve_id: str) -> Select[Any]:
        return select(_TABLE).where(
            (_TABLE.c.study_id == self._study_id)
            & (_TABLE.c.area_id == area_id)
            & (_TABLE.c.thermal_id == thermal_id)
            & (_TABLE.c.reserve_id == reserve_id)
        )

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def get_all_thermal_reserve_certifications(self) -> ThermalReserveCertificationsMapping:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalReserveCertificationsMapping = {}
        for row in rows:
            certification = _convert_row_to_model(row)
            result.setdefault(row.area_id, {}).setdefault(row.thermal_id, {})[row.reserve_id] = certification
        return result

    @override
    def get_all_thermal_reserve_certifications_for_cluster(
            self, area_id: AreaId, thermal_id: ThermalId
    ) -> dict[ReserveDefinitionId, ThermalReserveCertification]:
        stmt = select(_TABLE).where(
            (_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id) & (_TABLE.c.thermal_id == thermal_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        return {row.reserve_id: _convert_row_to_model(row) for row in rows}

    @override
    def get_thermal_reserve_certification(self, area_id: AreaId, thermal_id: ThermalId, reserve_id: ReserveDefinitionId) -> ThermalReserveCertification:
        row = self._db_session.execute(self._select_one(area_id, thermal_id, reserve_id)).fetchone()
        if row:
            return _convert_row_to_model(row)

        self._raise_the_right_thermal_reserve_exception({area_id: {thermal_id: {ReserveDefinitionId(reserve_id): ThermalReserveCertification()}}})

    @override
    def thermal_reserve_certification_exists(self, area_id: AreaId, thermal_id: ThermalId, reserve_id: ReserveDefinitionId) -> bool:
        return self._db_session.execute(self._select_one(area_id, thermal_id, reserve_id)).fetchone() is not None

    @override
    def save_thermal_reserve_certifications(
            self,
            data: dict[AreaId, dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]],
    ) -> None:
        if not data:
            return
        values = []
        for area_id, thermal_dict in data.items():
            for thermal_id, reserves_dict in thermal_dict.items():
                for reserve_id, certification in reserves_dict.items():
                    values.append(_convert_model_to_row(self._study_id, area_id, thermal_id, reserve_id, certification))
        try:
            upsert_multiple(session=self._db_session, table=_TABLE, values=values)
        except IntegrityError as e:
            self._raise_the_right_thermal_reserve_exception(data, exc=e)
        self._db_session.commit()

    @override
    def delete_thermal_reserve_certifications(self, area_id: AreaId, thermal_id: ThermalId,
                                              reserve_ids: list[ReserveDefinitionId]) -> None:
        if not reserve_ids:
            return

        result = self._db_session.execute(
            delete(_TABLE).where(
                (_TABLE.c.study_id == self._study_id)
                & (_TABLE.c.area_id == area_id)
                & (_TABLE.c.thermal_id == thermal_id)
                & (_TABLE.c.reserve_id.in_(reserve_ids))
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount < len(reserve_ids):
            existing_reserve_ids = set(self.get_all_thermal_reserve_certifications_for_cluster(area_id, thermal_id))
            for rid in reserve_ids:
                if rid not in existing_reserve_ids:
                    raise ThermalReserveCertificationNotFound(area_id, thermal_id, reserve_id=rid)
        self._db_session.commit()

    def _raise_the_right_thermal_reserve_exception(
        self, data: dict[AreaId, dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertification]]], exc: IntegrityError | None = None
    ) -> NoReturn:
        # Checks if some areas are missing
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

        # Checks if some thermals are missing
        all_existing_thermals = self.get_impl().get_all_thermals()
        invalid_thermal_dict = {}
        for area_id in data:
            if invalid_thermals := set(data[area_id]) - set(all_existing_thermals.get(area_id, [])):
                invalid_thermal_dict[area_id] = invalid_thermals

        if invalid_thermal_dict:
            raise ThermalClustersNotFound(invalid_thermal_dict) from exc

        # Checks if some reserve definitions are missing
        all_existing_reserves = self.get_impl().get_all_reserve_definitions()
        invalid_reserves_dict = {}
        for area_id, thermal_dict in data.items():
            for reserves_dict in thermal_dict.values():
                if invalid_reserves := set(reserves_dict) - set(all_existing_reserves.get(area_id, {})):
                    invalid_reserves_dict[area_id] = invalid_reserves

        if invalid_reserves_dict:
            raise ReserveDefinitionsNotFound(invalid_reserves_dict)  # type: ignore

        # All reserves exist. It means that the DB table does not contain the information.
        raise ValueError("One of the thermal reserve certification table is not filled as it should") from exc
