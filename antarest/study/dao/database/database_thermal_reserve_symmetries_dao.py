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

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetry, merge_symmetries
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
    def set_thermal_reserve_symmetries(
        self, area_id: AreaId, thermal_id: ThermalId, symmetries: list[ReserveSymmetry]
    ) -> None:
        existing_reserve_definitions = self.get_impl().get_all_reserve_definitions_for_area(area_id)
        reserve_ids = [ReserveDefinitionId(reserve.id) for reserve in existing_reserve_definitions]
        self._checks_foreign_key_integrity({area_id: {thermal_id: symmetries}}, {area_id: reserve_ids})
        # todo: continue

    @override
    def save_all_thermal_reserve_symmetries(self, data: ThermalReserveSymmetriesMapping) -> None:
        existing_reserve_definitions = self.get_impl().get_all_reserve_definitions()
        existing_reserve_ids = {}
        for area_id, value in existing_reserve_definitions.items():
            existing_reserve_ids[area_id] = list(value)
        self._checks_foreign_key_integrity(data, existing_reserve_ids)
        # todo: continue
        raise NotImplementedError()

    @staticmethod
    def _checks_foreign_key_integrity(
        new_data: ThermalReserveSymmetriesMapping, reserve_ids: dict[AreaId, ReserveSymmetry]
    ) -> None:
        """
        There is no foreign key constraint between symmetries and reserve ids but they are linked.
        So we have to check the data integrity manually.
        """
        for area_id, value in new_data.items():
            for symmetries in value.values():
                for symmetry in symmetries:
                    for reserve_id in symmetry:
                        if reserve_id not in reserve_ids[area_id]:
                            raise ValueError(f"Invalid reserve id {reserve_id} for area {area_id}")
