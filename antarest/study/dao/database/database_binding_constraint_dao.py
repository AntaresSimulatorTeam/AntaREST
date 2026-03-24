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

"""
Database implementation of ConstraintDao.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl
from sqlalchemy import Table, delete, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import outerjoin
from typing_extensions import override

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.business.model.common import join_with_comma
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_CLUSTER_TERM_TABLE,
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_LINK_TERM_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_multiple, upsert_one

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseBindingConstraintDao(ConstraintDao):
    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        raise NotImplementedError()

    def _fetch_constraints(self, constraint_id: str | None = None) -> dict[str, BindingConstraint]:
        """
        Two steps in this function
        Step 1 : BC LEFT JOIN link_terms builds the result dict: one entry per constraint, pre-populated with
        its BC fields and link terms.
        Step 2 : BC LEFT JOIN cluster_terms fetches cluster_terms and appends them.

        Two round trips, but joining both term tables at once would produce a Cartesian product,
        that would make us fetch more data and process more data also we'll need to handle de-duplication which would make the code less readable."""
        db = self._db_session
        BC = BINDING_CONSTRAINT_TABLE
        LT = BINDING_CONSTRAINT_LINK_TERM_TABLE
        CT = BINDING_CONSTRAINT_CLUSTER_TERM_TABLE

        # Query 1: BC left join link terms
        link_join = outerjoin(
            BC,
            LT,
            (BC.c.study_id == LT.c.study_id) & (BC.c.constraint_id == LT.c.constraint_id),
        )
        q1 = (
            select(
                BC.c.constraint_id,
                BC.c.name,
                BC.c.enabled,
                BC.c.time_step,
                BC.c.operator,
                BC.c.comments,
                BC.c.filter_year_by_year,
                BC.c.filter_synthesis,
                BC.c.group,
                LT.c.area1,
                LT.c.area2,
                LT.c.weight.label("lt_weight"),
                LT.c.offset.label("lt_offset"),
            )
            .select_from(link_join)
            .where(BC.c.study_id == self._study_id)
        )
        if constraint_id is not None:
            q1 = q1.where(BC.c.constraint_id == constraint_id)

        bc_rows: dict[str, Any] = {}
        terms: dict[str, list[ConstraintTerm]] = {}

        for row in db.execute(q1).fetchall():
            cid = row.constraint_id
            if cid not in bc_rows:
                bc_rows[cid] = row
                terms[cid] = []
            if row.area1 is not None:
                terms[cid].append(
                    ConstraintTerm(
                        weight=row.lt_weight, offset=row.lt_offset, data=LinkTerm(area1=row.area1, area2=row.area2)
                    )
                )

        if not bc_rows:
            return {}

        # Query 2: cluster terms only (BC already fetched above)
        ct_filter = CT.c.study_id == self._study_id
        if constraint_id is not None:
            ct_filter = ct_filter & (CT.c.constraint_id == constraint_id)

        for row in db.execute(select(CT).where(ct_filter)).fetchall():
            terms[row.constraint_id].append(
                ConstraintTerm(
                    weight=row.weight, offset=row.offset, data=ClusterTerm(area=row.area, cluster=row.cluster)
                )
            )

        return {cid: self._row_to_bc(bc_rows[cid], terms[cid]) for cid in bc_rows}

    @staticmethod
    def _row_to_bc(row: Any, terms: list[ConstraintTerm]) -> BindingConstraint:
        return BindingConstraint(
            id=row.constraint_id,
            name=row.name,
            enabled=row.enabled,
            time_step=row.time_step,
            operator=row.operator,
            comments=row.comments,
            filter_year_by_year=row.filter_year_by_year,
            filter_synthesis=row.filter_synthesis,
            group=row.group,
            terms=terms,
        )

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        return self._fetch_constraints()

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        result = self._fetch_constraints(constraint_id)
        if not result:
            raise BindingConstraintNotFound(f"Constraint {constraint_id} not found")
        return result[constraint_id]

    def _get_bc_matrix(self, constraint_id: str, table: Table) -> pl.DataFrame:
        row = self._db_session.execute(
            select(table).where((table.c.study_id == self._study_id) & (table.c.constraint_id == constraint_id))
        ).fetchone()
        if row is None:
            raise BindingConstraintNotFound(f"Matrix for constraint {constraint_id} not found")
        return self.get_impl().get_matrix(row.matrix_id)

    def _save_bc_matrix(self, constraint_id: str, table: Table, series_id: str) -> None:
        upsert_one(
            self._db_session,
            table,
            {"study_id": self._study_id, "constraint_id": constraint_id, "matrix_id": series_id},
        )
        self._db_session.commit()

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._get_bc_matrix(constraint_id, BINDING_CONSTRAINT_VALUES_MATRIX_TABLE)

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._get_bc_matrix(constraint_id, BINDING_CONSTRAINT_LT_MATRIX_TABLE)

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._get_bc_matrix(constraint_id, BINDING_CONSTRAINT_GT_MATRIX_TABLE)

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._get_bc_matrix(constraint_id, BINDING_CONSTRAINT_EQ_MATRIX_TABLE)

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        db = self._db_session

        constraint_ids = [bc.id for bc in constraints]

        # ===== Constraint Table
        db.execute(
            delete(BINDING_CONSTRAINT_TABLE).where(
                (BINDING_CONSTRAINT_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_TABLE.c.constraint_id.not_in(constraint_ids))
            )
        )
        upsert_multiple(db, BINDING_CONSTRAINT_TABLE, [self._bc_to_row(self._study_id, bc) for bc in constraints])

        # ===== Cluster Term Table
        cluster_terms = [
            self._cluster_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, ClusterTerm)
        ]
        db.execute(
            delete(BINDING_CONSTRAINT_CLUSTER_TERM_TABLE).where(
                (BINDING_CONSTRAINT_CLUSTER_TERM_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_CLUSTER_TERM_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )
        upsert_multiple(db, BINDING_CONSTRAINT_CLUSTER_TERM_TABLE, cluster_terms)

        # ===== Link Term Table
        link_terms = [
            self._link_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, LinkTerm)
        ]
        db.execute(
            delete(BINDING_CONSTRAINT_LINK_TERM_TABLE).where(
                (BINDING_CONSTRAINT_LINK_TERM_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_LINK_TERM_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )
        upsert_multiple(db, BINDING_CONSTRAINT_LINK_TERM_TABLE, link_terms)

        db.commit()

    def _bc_to_row(self, study_id: str, bc: BindingConstraint) -> dict[str, Any]:
        return {
            "study_id": study_id,
            "constraint_id": bc.id,
            "name": bc.name,
            "enabled": bc.enabled,
            "time_step": bc.time_step,
            "operator": bc.operator,
            "comments": bc.comments,
            "filter_year_by_year": join_with_comma(bc.filter_year_by_year)
            if bc.filter_year_by_year is not None
            else None,
            "filter_synthesis": join_with_comma(bc.filter_synthesis) if bc.filter_synthesis is not None else None,
            "group": bc.group,
        }

    def _cluster_term_to_row(self, study_id: str, constraint_id: str, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, ClusterTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            "weight": term.weight,
            "offset": term.offset,
            "area": term.data.area,
            "cluster": term.data.cluster,
        }

    def _link_term_to_row(self, study_id: str, constraint_id: str, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, LinkTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            "weight": term.weight,
            "offset": term.offset,
            "area1": term.data.area1,
            "area2": term.data.area2,
        }

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrix(constraint_id, BINDING_CONSTRAINT_VALUES_MATRIX_TABLE, series_id)

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrix(constraint_id, BINDING_CONSTRAINT_LT_MATRIX_TABLE, series_id)

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrix(constraint_id, BINDING_CONSTRAINT_GT_MATRIX_TABLE, series_id)

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrix(constraint_id, BINDING_CONSTRAINT_EQ_MATRIX_TABLE, series_id)

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        db = self._db_session
        constraint_ids = [bc.id for bc in constraints]
        db.execute(
            delete(BINDING_CONSTRAINT_TABLE).where(
                (BINDING_CONSTRAINT_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )
        db.commit()
