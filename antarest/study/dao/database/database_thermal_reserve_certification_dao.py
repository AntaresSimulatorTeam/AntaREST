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

from sqlalchemy import Row, Select, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveDefinitionsNotFound,
    ThermalClustersNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertification,
    ThermalReserveCertificationMapping,
)
from antarest.study.dao.api.thermal_reserve_certification_dao import ThermalReserveCertificationDao
from antarest.study.dao.common import AreaId, ThermalId
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.thermal_reserve_certification import THERMAL_RESERVE_CERTIFICATION_TABLE

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
    def get_all_thermal_reserve_certifications(self) -> dict[AreaId, ThermalReserveCertificationMapping]:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: dict[AreaId, ThermalReserveCertificationMapping] = {}
        for row in rows:
            certification = _convert_row_to_model(row)
            result.setdefault(row.area_id, {}).setdefault(row.thermal_id, {})[row.reserve_id] = certification
        return result

    @override
    def get_all_thermal_reserve_certifications_for_area(
        self, area_id: AreaId
    ) -> dict[ReserveDefinitionId, dict[ThermalId, ThermalReserveCertification]]:
        stmt = select(_TABLE).where((_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        return {row.reserve_id: {row.thermal_id: _convert_row_to_model(row)} for row in rows}

    @override
    def save_thermal_reserve_certifications(self, data: dict[AreaId, ThermalReserveCertificationMapping]) -> None:
        if not data:
            return
        values = []
        for area_id, reserves_dict in data.items():
            for reserve_id, thermal_dict in reserves_dict.items():
                for thermal_id, certification in thermal_dict.items():
                    values.append(_convert_model_to_row(self._study_id, area_id, thermal_id, reserve_id, certification))
        try:
            # First, clean the DB
            area_ids = set(data)
            reserve_ids = {reserve_id for area_id, reserves_dict in data.items() for reserve_id in reserves_dict}
            stmt = delete(_TABLE).where(
                (_TABLE.c.study_id == self._study_id)
                & (_TABLE.c.area_id.in_(area_ids))
                & _TABLE.c.reserve_id.in_(reserve_ids)
            )
            self._db_session.execute(stmt)
            # Then, insert the new values
            self._db_session.execute(insert(_TABLE), values)
        except IntegrityError as e:
            self._raise_the_right_thermal_reserve_exception(data, exc=e)
        self._db_session.commit()

    def _raise_the_right_thermal_reserve_exception(
        self,
        data: dict[AreaId, ThermalReserveCertificationMapping],
        exc: IntegrityError | None = None,
    ) -> NoReturn:
        # Checks if some areas are missing
        existing_ids = set(self.get_impl().get_all_area_ids())
        if invalid_areas := set(data) - existing_ids:
            raise AreaNotFound(*invalid_areas)

        # Checks if some reserve definitions are missing
        all_existing_reserves = self.get_impl().get_all_reserve_definitions()
        invalid_reserves_dict = {}
        for area_id, reserves_dict in data.items():
            if invalid_reserves := set(reserves_dict) - set(all_existing_reserves.get(area_id, {})):
                invalid_reserves_dict[area_id] = invalid_reserves

        if invalid_reserves_dict:
            raise ReserveDefinitionsNotFound(invalid_reserves_dict)  # type: ignore

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
