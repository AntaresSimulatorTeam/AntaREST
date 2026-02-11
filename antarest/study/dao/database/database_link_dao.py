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
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl
from sqlalchemy import Insert, Row, Table, Update, delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, LinkNotFound
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.link_model import Link
from antarest.study.dao.api.link_dao import LinkDao
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.link import (
    LINK_DIRECT_CAPACITY_TABLE,
    LINK_INDIRECT_CAPACITY_TABLE,
    LINK_SERIES_TABLE,
    LINK_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def _join_with_comma(values: list[FilterOption]) -> str:
    """Serialize filtering values for DB format"""
    return ", ".join(value.name.lower() for value in values)


def _convert_db_rows_to_model(db_row: Any) -> Link:
    data = get_row_representation_as_dict(db_row)
    del data["study_id"]
    return Link(**data)


class DatabaseLinkDao(LinkDao):
    """Database implementation of LinkDao"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    @override
    def save_link(self, link: Link) -> None:
        session = self.get_session()
        values = dict(study_id=self.get_study_id(), **link.model_dump())

        try:
            upsert_one(session, LINK_TABLE, values)
        except IntegrityError:
            # Happens if the link's areas did not existed -> ForeignKey constraint fails
            session.rollback()
            raise AreaNotFound(*[link.area1, link.area2])

        session.commit()

    @override
    def delete_link(self, link: Link) -> None:
        if not self.link_exists(link.area1, link.area2):
            raise LinkNotFound(f"The link {link.area1} -> {link.area2} is not present in the study")

        study_id = self.get_study_id()
        session = self.get_session()
        stmt = delete(LINK_TABLE).where(
            (LINK_TABLE.c.study_id == study_id)
            & (LINK_TABLE.c.area1 == link.area1)
            & (LINK_TABLE.c.area2 == link.area2)
        )
        session.execute(stmt)
        session.commit()

    @override
    def get_links(self) -> Sequence[Link]:
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(LINK_TABLE).where((LINK_TABLE.c.study_id == study_id))
        rows = session.execute(stmt).fetchall()
        return [_convert_db_rows_to_model(row) for row in rows]

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        row = self._get_row(area1_id, area2_id, LINK_TABLE)
        if not row:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")
        return _convert_db_rows_to_model(row)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        row = self._get_row(area1_id, area2_id, LINK_TABLE)
        return row is not None

    def _get_row(self, area1_id: str, area2_id: str, table: Table) -> Row[Any] | None:
        area1, area2 = sorted((area1_id, area2_id))
        study_id = self.get_study_id()
        session = self.get_session()
        stmt = select(table).where((table.c.study_id == study_id) & (table.c.area1 == area1) & (table.c.area2 == area2))
        return session.execute(stmt).fetchone()

    def _get_link_matrix(self, area_from_id: str, area_to_id: str, table: Table) -> pl.DataFrame:
        row = self._get_row(area_from_id, area_to_id, table)
        if not row:
            raise LinkNotFound(f"The link {area_from_id} -> {area_to_id} is not present in the study")
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_link_matrix(self, area_from_id: str, area_to_id: str, table: Table, matrix_id: str) -> None:
        area1, area2 = sorted((area_from_id, area_to_id))
        row = self._get_row(area1, area2, table)
        session = self.get_session()
        study_id = self.get_study_id()
        stmt: Insert | Update
        if not row:
            # We must check if the link exist or not
            if not self.link_exists(area1, area2):
                raise LinkNotFound(f"The link {area1} -> {area2} is not present in the study")
            stmt = insert(table).values(study_id=study_id, area1=area1, area2=area2, matrix_id=matrix_id)
        else:
            stmt = (
                update(table)
                .where((table.c.study_id == study_id) & (table.c.area1 == area1) & (table.c.area2 == area2))
                .values(matrix_id=matrix_id)
            )

        session.execute(stmt)
        session.commit()

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._save_link_matrix(area_from, area_to, LINK_INDIRECT_CAPACITY_TABLE, series_id)

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._save_link_matrix(area_from, area_to, LINK_DIRECT_CAPACITY_TABLE, series_id)

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        self._save_link_matrix(area_from, area_to, LINK_SERIES_TABLE, series_id)

    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._get_link_matrix(area_from, area_to, LINK_DIRECT_CAPACITY_TABLE)

    @override
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._get_link_matrix(area_from, area_to, LINK_INDIRECT_CAPACITY_TABLE)

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._get_link_matrix(area_from, area_to, LINK_SERIES_TABLE)
