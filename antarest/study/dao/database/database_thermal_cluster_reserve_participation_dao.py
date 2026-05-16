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

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ThermalClusterReserveParticipationNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)
from antarest.study.dao.api.thermal_cluster_reserve_participation_dao import (
    ThermalClusterReserveParticipationDao,
)
from antarest.study.dao.common import AreaId, ThermalClusterReserveParticipationsMapping, ThermalId
from antarest.study.dao.database.common import area_exists, get_row_representation_as_dict, validate_area_exists
from antarest.study.dao.database.models.thermal_cluster_reserve_participation import (
    THERMAL_CLUSTER_RESERVE_PARTICIPATION_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple

_TABLE = THERMAL_CLUSTER_RESERVE_PARTICIPATION_TABLE


def _convert_row_to_model(row: Row[Any]) -> ThermalClusterReserveParticipation:
    data = get_row_representation_as_dict(row)
    for key in ("study_id", "area_id", "thermal_id"):
        data.pop(key, None)
    data["id"] = data.pop("reserve_id")
    return ThermalClusterReserveParticipation.model_validate(data)


def _convert_model_to_row(
    study_id: str, area_id: str, thermal_id: str, participation: ThermalClusterReserveParticipation
) -> dict[str, Any]:
    values = participation.model_dump()
    values["reserve_id"] = values.pop("id")
    values["study_id"] = study_id
    values["area_id"] = area_id
    values["thermal_id"] = thermal_id
    return values


class DatabaseThermalClusterReserveParticipationDao(ThermalClusterReserveParticipationDao):
    """Database implementation of ThermalClusterReserveParticipationDao."""

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

    @override
    def get_all_thermal_cluster_reserve_participations(self) -> ThermalClusterReserveParticipationsMapping:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ThermalClusterReserveParticipationsMapping = {}
        for row in rows:
            participation = _convert_row_to_model(row)
            result.setdefault(row.area_id, {}).setdefault(row.thermal_id, {})[ReserveDefinitionId(participation.id)] = (
                participation
            )
        return result

    @override
    def get_all_thermal_cluster_reserve_participations_for_cluster(
        self, area_id: str, thermal_id: str
    ) -> Sequence[ThermalClusterReserveParticipation]:
        stmt = select(_TABLE).where(
            (_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id) & (_TABLE.c.thermal_id == thermal_id)
        )
        rows = self._db_session.execute(stmt).fetchall()
        if not rows:
            validate_area_exists(self._db_session, self._study_id, area_id)
        return [_convert_row_to_model(row) for row in rows]

    @override
    def get_thermal_cluster_reserve_participation(
        self, area_id: str, thermal_id: str, reserve_id: str
    ) -> ThermalClusterReserveParticipation:
        row = self._db_session.execute(self._select_one(area_id, thermal_id, reserve_id)).fetchone()
        if not row:
            validate_area_exists(self._db_session, self._study_id, area_id)
            raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, reserve_id)
        return _convert_row_to_model(row)

    @override
    def thermal_cluster_reserve_participation_exists(self, area_id: str, thermal_id: str, reserve_id: str) -> bool:
        return self._db_session.execute(self._select_one(area_id, thermal_id, reserve_id)).fetchone() is not None

    @override
    def save_thermal_cluster_reserve_participations(
        self,
        data: dict[AreaId, dict[ThermalId, list[ThermalClusterReserveParticipation]]],
    ) -> None:
        if not data:
            return
        values = []
        for area_id, by_cluster in data.items():
            for thermal_id, participations in by_cluster.items():
                for participation in participations:
                    values.append(_convert_model_to_row(self._study_id, area_id, thermal_id, participation))
        if not values:
            return
        try:
            upsert_multiple(session=self._db_session, table=_TABLE, values=values)
        except IntegrityError as e:
            for area_id in data:
                if not area_exists(self._db_session, self._study_id, area_id):
                    raise AreaNotFound(area_id) from e
            raise
        self._db_session.commit()

    @override
    def delete_thermal_cluster_reserve_participations(
        self,
        area_id: AreaId,
        thermal_id: ThermalId,
        reserve_ids: Sequence[ReserveDefinitionId],
    ) -> None:
        if not reserve_ids:
            return
        existing = {
            row.reserve_id
            for row in self._db_session.execute(
                select(_TABLE.c.reserve_id).where(
                    (_TABLE.c.study_id == self._study_id)
                    & (_TABLE.c.area_id == area_id)
                    & (_TABLE.c.thermal_id == thermal_id)
                    & (_TABLE.c.reserve_id.in_(reserve_ids))
                )
            ).fetchall()
        }
        for rid in reserve_ids:
            if rid not in existing:
                raise ThermalClusterReserveParticipationNotFound(area_id, thermal_id, rid)
        self._db_session.execute(
            delete(_TABLE).where(
                (_TABLE.c.study_id == self._study_id)
                & (_TABLE.c.area_id == area_id)
                & (_TABLE.c.thermal_id == thermal_id)
                & (_TABLE.c.reserve_id.in_(reserve_ids))
            )
        )
        self._db_session.commit()
