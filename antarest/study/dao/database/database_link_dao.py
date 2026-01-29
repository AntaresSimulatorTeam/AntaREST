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
from sqlalchemy import Row, delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, LinkNotFound
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.link_model import Link
from antarest.study.dao.api.link_dao import LinkDao
from antarest.study.dao.database.models.link import LINK_TABLE

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def _join_with_comma(values: list[FilterOption]) -> str:
    """Serialize filtering values for DB format"""
    return ", ".join(value.name.lower() for value in values)


def _convert_db_rows_to_model(db_row: Any) -> Link:
    return Link(
        area1=db_row.area1,
        area2=db_row.area2,
        hurdles_cost=db_row.hurdles_cost,
        loop_flow=db_row.loop_flow,
        use_phase_shifter=db_row.use_phase_shifter,
        transmission_capacities=db_row.transmission_capacities,
        asset_type=db_row.asset_type,
        display_comments=db_row.display_comments,
        comments=db_row.comments,
        colorr=db_row.colorr,
        colorb=db_row.colorb,
        colorg=db_row.colorg,
        link_width=db_row.link_width,
        link_style=db_row.link_style,
        filter_synthesis=db_row.filter_synthesis,
        filter_year_by_year=db_row.filter_year_by_year,
    )


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

        values = {
            "hurdles_cost": link.hurdles_cost,
            "loop_flow": link.loop_flow,
            "use_phase_shifter": link.use_phase_shifter,
            "transmission_capacities": link.transmission_capacities,
            "asset_type": link.asset_type,
            "display_comments": link.display_comments,
            "comments": link.comments,
            "colorr": link.colorr,
            "colorb": link.colorb,
            "colorg": link.colorg,
            "link_width": link.link_width,
            "link_style": link.link_style,
            "filter_synthesis": _join_with_comma(link.filter_synthesis),
            "filter_year_by_year": _join_with_comma(link.filter_year_by_year),
        }

        if self.link_exists(link.area1, link.area2):
            stmt_update = (
                update(LINK_TABLE)
                .where(
                    (LINK_TABLE.c.study_id == self.get_study_id())
                    & (LINK_TABLE.c.area1 == link.area1)
                    & (LINK_TABLE.c.area2 == link.area2)
                )
                .values(values)
            )

            session.execute(stmt_update)
        else:
            values["study_id"] = self.get_study_id()
            values["area1"] = link.area1
            values["area2"] = link.area2
            stmt_insert = insert(LINK_TABLE).values(values)

            try:
                session.execute(stmt_insert)
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
        row = self._get_link_row(area1_id, area2_id)
        if not row:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")
        return _convert_db_rows_to_model(row)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        row = self._get_link_row(area1_id, area2_id)
        return row is not None

    def _get_link_row(self, area1_id: str, area2_id: str) -> Row[Any] | None:
        study_id = self.get_study_id()
        session = self.get_session()

        stmt = select(LINK_TABLE).where(
            (LINK_TABLE.c.study_id == study_id) & (LINK_TABLE.c.area1 == area1_id) & (LINK_TABLE.c.area2 == area2_id)
        )

        return session.execute(stmt).fetchone()

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
