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
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX
from antarest.study.business.model.binding_constraint_model import (
    OPERATOR_MATRICES_MAP,
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
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
from antarest.study.dao.database.models.ruleset import SCENARIO_BINDING_CONSTRAINTS_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple
from antarest.study.model import STUDY_VERSION_8_7

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

    def _save_bc_matrices(self, table: Table, entries: list[tuple[str, str]]) -> None:
        rows = [{"study_id": self._study_id, "constraint_id": cid, "matrix_id": mid} for cid, mid in entries]
        upsert_multiple(self._db_session, table, rows)
        self._db_session.commit()

    def _delete_bc_matrices(self, table: Table, constraint_ids: list[str]) -> None:
        self._db_session.execute(
            delete(table).where((table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids)))
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
        impl = self.get_impl()
        study_version = impl.get_version()
        constants = impl._generator_matrix_constants

        constraint_ids = [bc.id for bc in constraints]

        # Fetch existing constraints BEFORE upserting (needed for change detection)
        existing = self._fetch_constraints()

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

        # ===== Matrix updates
        _TERM_TABLE: dict[str, Table] = {
            "lt": BINDING_CONSTRAINT_LT_MATRIX_TABLE,
            "gt": BINDING_CONSTRAINT_GT_MATRIX_TABLE,
            "eq": BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
            "values": BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
        }
        to_delete: dict[str, list[str]] = {t: [] for t in _TERM_TABLE}
        to_create: dict[str, list[tuple[str, str]]] = {t: [] for t in _TERM_TABLE}

        # Fetch all existing matrix IDs upfront — needed for operator change (copy source)
        existing_matrix_ids: dict[str, dict[str, str]] = {}
        for term, table in _TERM_TABLE.items():
            rows = db.execute(
                select(table.c.constraint_id, table.c.matrix_id).where(
                    (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids))
                )
            ).fetchall()
            for row in rows:
                existing_matrix_ids.setdefault(row.constraint_id, {})[term] = row.matrix_id

        def _default_matrix_id(time_step: BindingConstraintFrequency) -> str:
            if study_version < STUDY_VERSION_8_7:
                uri = {
                    BindingConstraintFrequency.HOURLY: constants.get_binding_constraint_hourly_86,
                    BindingConstraintFrequency.DAILY: constants.get_binding_constraint_daily_weekly_86,
                    BindingConstraintFrequency.WEEKLY: constants.get_binding_constraint_daily_weekly_86,
                }[time_step]()
            else:
                uri = {
                    BindingConstraintFrequency.HOURLY: constants.get_binding_constraint_hourly_87,
                    BindingConstraintFrequency.DAILY: constants.get_binding_constraint_daily_weekly_87,
                    BindingConstraintFrequency.WEEKLY: constants.get_binding_constraint_daily_weekly_87,
                }[time_step]()
            return uri.removeprefix(MATRIX_PROTOCOL_PREFIX)

        for bc in constraints:
            old = existing.get(bc.id)
            if old is None:
                continue  # new constraint — caller handles initial matrix creation

            time_step_changed = bc.time_step != old.time_step
            operator_changed = study_version >= STUDY_VERSION_8_7 and bc.operator != old.operator

            if time_step_changed:
                # Reset all matrices to zero defaults for the new time step.
                # If both time step and operator changed, the result is zeros anyway.
                default_mid = _default_matrix_id(bc.time_step)
                if study_version < STUDY_VERSION_8_7:
                    to_delete["values"].append(bc.id)
                    to_create["values"].append((bc.id, default_mid))
                else:
                    for term in OPERATOR_MATRICES_MAP[old.operator]:
                        to_delete[term].append(bc.id)
                    for term in OPERATOR_MATRICES_MAP[bc.operator]:
                        to_create[term].append((bc.id, default_mid))

            elif operator_changed:
                # Copy/move matrix data between tables without resetting values.
                old_terms = OPERATOR_MATRICES_MAP[old.operator]
                new_terms = OPERATOR_MATRICES_MAP[bc.operator]
                terms_to_add = [t for t in new_terms if t not in old_terms]
                terms_to_del = [t for t in old_terms if t not in new_terms]

                if terms_to_add:
                    # For BOTH, lt is the canonical source (mirrors file DAO rename logic).
                    # For single operators, there is only one term so it is unambiguous.
                    source_term = "lt" if old.operator == BindingConstraintOperator.BOTH else old_terms[0]
                    source_mid = existing_matrix_ids.get(bc.id, {}).get(source_term)
                    if source_mid is None:
                        source_mid = _default_matrix_id(old.time_step)
                    for term in terms_to_add:
                        to_create[term].append((bc.id, source_mid))

                for term in terms_to_del:
                    to_delete[term].append(bc.id)

        # Apply deletes first, then creates, within the same transaction
        for term, table in _TERM_TABLE.items():
            if to_delete[term]:
                db.execute(
                    delete(table).where(
                        (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(to_delete[term]))
                    )
                )
        for term, table in _TERM_TABLE.items():
            if to_create[term]:
                upsert_multiple(
                    db,
                    table,
                    [
                        {"study_id": self._study_id, "constraint_id": cid, "matrix_id": mid}
                        for cid, mid in to_create[term]
                    ],
                )

        # ===== Scenario builder group cleanup
        new_groups = {bc.group for bc in constraints if bc.group}
        old_groups = {bc.group for bc in existing.values() if bc.group}
        removed_groups = old_groups - new_groups
        if removed_groups:
            db.execute(
                delete(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                    (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == self._study_id)
                    & (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.bc_group_id.in_(removed_groups))
                )
            )

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
        self._save_bc_matrices(BINDING_CONSTRAINT_VALUES_MATRIX_TABLE, [(constraint_id, series_id)])

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_LT_MATRIX_TABLE, [(constraint_id, series_id)])

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_GT_MATRIX_TABLE, [(constraint_id, series_id)])

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_EQ_MATRIX_TABLE, [(constraint_id, series_id)])

    def delete_constraint_values_matrix(self, constraint_id: str) -> None:
        self._delete_bc_matrices(BINDING_CONSTRAINT_VALUES_MATRIX_TABLE, [constraint_id])

    def delete_constraint_less_term_matrix(self, constraint_id: str) -> None:
        self._delete_bc_matrices(BINDING_CONSTRAINT_LT_MATRIX_TABLE, [constraint_id])

    def delete_constraint_greater_term_matrix(self, constraint_id: str) -> None:
        self._delete_bc_matrices(BINDING_CONSTRAINT_GT_MATRIX_TABLE, [constraint_id])

    def delete_constraint_equal_term_matrix(self, constraint_id: str) -> None:
        self._delete_bc_matrices(BINDING_CONSTRAINT_EQ_MATRIX_TABLE, [constraint_id])

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
