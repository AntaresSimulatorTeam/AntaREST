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
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import polars as pl
from sqlalchemy import CursorResult, Row, Select, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveDefinitionId
from antarest.study.dao.api.reserve_definition_dao import ReserveDefinitionDao
from antarest.study.dao.common import AreaId, ReserveDefinitionsMapping, ReserveNeedsMapping
from antarest.study.dao.database.common import area_exists, get_row_representation_as_dict, validate_area_exists
from antarest.study.dao.database.models.reserve_definition import RESERVE_DEFINITION_TABLE
from antarest.study.dao.database.models.reserve_need import RESERVE_NEED_MATRIX_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao

_TABLE = RESERVE_DEFINITION_TABLE
_NEED_TABLE = RESERVE_NEED_MATRIX_TABLE


def _convert_row_to_model(row: Row[Any]) -> ReserveDefinition:
    data = get_row_representation_as_dict(row)
    del data["study_id"]
    del data["area_id"]
    data["id"] = data.pop("reserve_id")
    return ReserveDefinition.model_validate(data)


def _convert_model_to_row(study_id: str, area_id: str, reserve: ReserveDefinition) -> dict[str, Any]:
    values = reserve.model_dump()
    values["reserve_id"] = values.pop("id")
    values["study_id"] = study_id
    values["area_id"] = area_id
    return values


class DatabaseReserveDefinitionDao(ReserveDefinitionDao):
    """Database implementation of ReserveDefinitionDao."""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _select_reserve(self, area_id: str, reserve_id: str) -> Select[Any]:
        return select(_TABLE).where(
            (_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id) & (_TABLE.c.reserve_id == reserve_id)
        )

    @override
    def get_all_reserve_definitions(self) -> ReserveDefinitionsMapping:
        stmt = select(_TABLE).where(_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ReserveDefinitionsMapping = {}
        for row in rows:
            reserve = _convert_row_to_model(row)
            result.setdefault(row.area_id, {})[ReserveDefinitionId(reserve.id)] = reserve
        return result

    @override
    def get_all_reserve_definitions_for_area(self, area_id: str) -> Sequence[ReserveDefinition]:
        stmt = select(_TABLE).where((_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id))
        rows = self._db_session.execute(stmt).fetchall()
        if not rows:
            validate_area_exists(self._db_session, self._study_id, area_id)
        return [_convert_row_to_model(row) for row in rows]

    @override
    def get_reserve_definition(self, area_id: str, reserve_id: str) -> ReserveDefinition:
        row = self._db_session.execute(self._select_reserve(area_id, reserve_id)).fetchone()
        if not row:
            validate_area_exists(self._db_session, self._study_id, area_id)
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        return _convert_row_to_model(row)

    @override
    def reserve_definition_exists(self, area_id: str, reserve_id: str) -> bool:
        return self._db_session.execute(self._select_reserve(area_id, reserve_id)).fetchone() is not None

    @override
    def save_reserve_definitions(self, data: dict[AreaId, list[ReserveDefinition]]) -> None:
        if not data:
            return

        values = []
        for area_id, reserves in data.items():
            for reserve in reserves:
                values.append(_convert_model_to_row(self._study_id, area_id, reserve))
        try:
            upsert_multiple(session=self._db_session, table=_TABLE, values=values)
        except IntegrityError as e:
            for area_id in data:
                if not area_exists(self._db_session, self._study_id, area_id):
                    raise AreaNotFound(area_id) from e
            raise
        self._db_session.commit()

    @override
    def delete_reserve_definitions(self, area_id: AreaId, reserve_ids: Sequence[ReserveDefinitionId]) -> None:
        if not reserve_ids:
            return
        result = self._db_session.execute(
            delete(_TABLE).where(
                (_TABLE.c.study_id == self._study_id)
                & (_TABLE.c.area_id == area_id)
                & (_TABLE.c.reserve_id.in_(reserve_ids))
            )
        )
        assert isinstance(result, CursorResult)
        if result.rowcount < len(reserve_ids):
            existing = {
                row.reserve_id
                for row in self._db_session.execute(
                    select(_TABLE.c.reserve_id).where(
                        (_TABLE.c.study_id == self._study_id) & (_TABLE.c.area_id == area_id)
                    )
                ).fetchall()
            }
            for rid in reserve_ids:
                if rid not in existing:
                    raise ReserveDefinitionNotFound(area_id, rid)
        self._db_session.commit()

    @override
    def get_reserve_need(self, area_id: str, reserve_id: str) -> pl.DataFrame:
        stmt = select(_NEED_TABLE).where(
            (_NEED_TABLE.c.study_id == self._study_id)
            & (_NEED_TABLE.c.area_id == area_id)
            & (_NEED_TABLE.c.reserve_id == reserve_id)
        )
        row = self._db_session.execute(stmt).fetchone()
        if not row:
            raise ReserveDefinitionNotFound(area_id, reserve_id)
        return self.get_impl().get_matrix(str(row.matrix_id), default_empty_supplier=None)

    @override
    def get_all_reserve_needs(self) -> ReserveNeedsMapping:
        stmt = select(_NEED_TABLE).where(_NEED_TABLE.c.study_id == self._study_id)
        rows = self._db_session.execute(stmt).fetchall()
        result: ReserveNeedsMapping = {}
        for row in rows:
            result.setdefault(row.area_id, {})[ReserveDefinitionId(row.reserve_id)] = row.matrix_id
        return result

    @override
    def save_reserve_need(self, mapping: ReserveNeedsMapping) -> None:
        if not mapping:
            return
        values = []
        for area_id, per_reserve in mapping.items():
            for reserve_id, matrix_id in per_reserve.items():
                values.append(
                    {
                        "study_id": self._study_id,
                        "area_id": area_id,
                        "reserve_id": reserve_id,
                        "matrix_id": extract_matrix_id(matrix_id),
                    }
                )
        try:
            upsert_multiple(session=self._db_session, table=_NEED_TABLE, values=values)
        except IntegrityError as e:
            for area_id, per_reserve in mapping.items():
                if not area_exists(self._db_session, self._study_id, area_id):
                    raise AreaNotFound(area_id) from e
                # Otherwise, the reserve definition does not exist yet (FK violation on (study, area, reserve)).
                for reserve_id in per_reserve:
                    raise ReserveDefinitionNotFound(area_id, reserve_id) from e
            raise
        self._db_session.commit()

    @override
    def delete_reserve_need(self, area_id: AreaId, reserve_id: ReserveDefinitionId) -> None:
        result = self._db_session.execute(
            delete(_NEED_TABLE).where(
                (_NEED_TABLE.c.study_id == self._study_id)
                & (_NEED_TABLE.c.area_id == area_id)
                & (_NEED_TABLE.c.reserve_id == reserve_id)
            )
        )
        assert isinstance(result, CursorResult)
        self._db_session.commit()
