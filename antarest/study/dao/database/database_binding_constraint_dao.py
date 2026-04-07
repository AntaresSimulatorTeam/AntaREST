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
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl
from antares.study.version import StudyVersion
from sqlalchemy import Row, Table, delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import outerjoin
from typing_extensions import override

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.study.business.model.binding_constraint_model import (
    DEFAULT_GROUP,
    OPERATOR_MATRICES_MAP,
    BindingConstraint,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
    initialize_binding_constraint,
)
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_CLUSTER_TERM_TABLE as CT,
)
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
)
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_LINK_TERM_TABLE as LT,
)
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_TABLE as BC,
)
from antarest.study.dao.database.models.ruleset import SCENARIO_BINDING_CONSTRAINTS_TABLE
from antarest.study.dao.database.sql_utils import upsert_multiple
from antarest.study.model import STUDY_VERSION_8_7


class _MatrixType(str, Enum):
    """The four matrix types that can be attached to a binding constraint."""

    LT = "lt"
    GT = "gt"
    EQ = "eq"
    VALUES = "values"


_MATRIX_TYPE_TABLES: dict["_MatrixType", Table] = {
    _MatrixType.LT: BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    _MatrixType.GT: BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    _MatrixType.EQ: BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    _MatrixType.VALUES: BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
}


@dataclass
class _MatrixDeletion:
    """Identifies a matrix row to remove: delete the <type> row for <constraint_id>."""

    constraint_id: str
    suffix: _MatrixType


@dataclass
class _MatrixInsertion:
    """Identifies a matrix row to create or overwrite: write <matrix_id> into the <type> table for <constraint_id>."""

    constraint_id: str
    suffix: _MatrixType
    matrix_id: str


@dataclass
class _MatrixChanges:
    """Accumulates matrix-table changes for a batch of constraint updates."""

    deletions: list[_MatrixDeletion] = field(default_factory=list)
    insertions: list[_MatrixInsertion] = field(default_factory=list)

    def add_deletion(self, constraint_id: str, suffix: _MatrixType) -> None:
        self.deletions.append(_MatrixDeletion(constraint_id, suffix))

    def add_insertion(self, constraint_id: str, suffix: _MatrixType, matrix_id: str) -> None:
        self.insertions.append(_MatrixInsertion(constraint_id, suffix, matrix_id))


if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseBindingConstraintDao(ConstraintDao):
    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _fetch_constraints(self, constraint_id: str | None = None) -> dict[str, BindingConstraint]:
        """
        Two steps in this function
        Step 1 : BC LEFT JOIN link_terms builds the result dict: one entry per constraint, pre-populated with
        its BC fields and link terms.
        Step 2 : BC LEFT JOIN cluster_terms fetches cluster_terms and appends them.

        Two round trips, but joining both term tables at once would produce a Cartesian product,
        that would make us fetch more data and process more data also we'll need to handle de-duplication which would make the code less readable."""
        db = self._db_session

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

        version = self.get_impl().get_version()
        return {cid: self._row_to_bc(bc_rows[cid], terms[cid], version) for cid in bc_rows}

    @staticmethod
    def _row_to_bc(row: Row[Any], terms: list[ConstraintTerm], version: StudyVersion) -> BindingConstraint:
        d = get_row_representation_as_dict(row)
        d["id"] = d.pop("constraint_id")
        d["terms"] = terms
        bc = BindingConstraint.model_validate(d, extra="allow")
        initialize_binding_constraint(bc, version)
        return bc

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
        changes = self._compute_matrix_changes(constraints)
        self._save_constraint_rows(constraints)
        self._save_cluster_terms(constraints)
        self._save_link_terms(constraints)
        self._apply_matrix_changes(changes)
        self._cleanup_scenario_builder_groups()

        self._db_session.commit()

    def _save_constraint_rows(self, constraints: Sequence[BindingConstraint]) -> None:
        upsert_multiple(
            self._db_session,
            BC,
            [self._bc_to_row(self._study_id, bc) for bc in constraints],
        )

    def _save_cluster_terms(self, constraints: Sequence[BindingConstraint]) -> None:
        constraint_ids = [bc.id for bc in constraints]
        cluster_terms = [
            self._cluster_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, ClusterTerm)
        ]
        if not cluster_terms:
            return
        self._db_session.execute(
            delete(CT).where((CT.c.study_id == self._study_id) & (CT.c.constraint_id.in_(constraint_ids)))
        )
        upsert_multiple(self._db_session, CT, cluster_terms)

    def _save_link_terms(self, constraints: Sequence[BindingConstraint]) -> None:
        constraint_ids = [bc.id for bc in constraints]
        link_terms = [
            self._link_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, LinkTerm)
        ]
        if not link_terms:
            return
        self._db_session.execute(
            delete(LT).where((LT.c.study_id == self._study_id) & (LT.c.constraint_id.in_(constraint_ids)))
        )
        upsert_multiple(self._db_session, LT, link_terms)

    def _fetch_existing_matrix_ids(self, constraint_ids: list[str]) -> dict[str, dict[str, str]]:
        """Fetch all existing matrix IDs upfront needed for operator change (copy source)."""
        existing_matrix_ids: dict[str, dict[str, str]] = {}
        for suffix, table in _MATRIX_TYPE_TABLES.items():
            rows = self._db_session.execute(
                select(table.c.constraint_id, table.c.matrix_id).where(
                    (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids))
                )
            ).fetchall()
            for row in rows:
                existing_matrix_ids.setdefault(row.constraint_id, {})[suffix.value] = row.matrix_id
        return existing_matrix_ids

    def _compute_matrix_changes(
        self,
        constraints: Sequence[BindingConstraint],
    ) -> _MatrixChanges:
        """Compute the matrix-table changes needed when constraints are updated.

        Skips new constraints.

        When a constraint operator is updated: each operator owns a specific set of
        matrix types (lt, gt, eq). We copy the existing matrix ID into any newly
        required matrix table and delete any type that is no longer needed,
        so user data is preserved rather than reset.

        When a time-step is updated: the matrix row count is tied to the frequency
        (hourly=8784 rows, daily/weekly=366 rows), so existing data would be the
        wrong shape. All affected matrix rows are replaced with the null matrix and
        the simulator fills in correctly-sized zeros at runtime.

        Examples::

            # Operator LESS → BOTH: lt data copied to new gt row, nothing deleted
            # Operator BOTH → LESS: gt row deleted, lt row keeps its data
            # Operator BOTH → EQUAL: lt data copied to new eq row, lt and gt deleted
            # Time-step HOURLY → DAILY: all matrix rows replaced with null matrix
            # Time-step + operator change: time-step reset takes precedence
        """
        impl = self.get_impl()
        study_version = impl.get_version()
        existing = self._fetch_constraints()
        existing_matrix_ids = self._fetch_existing_matrix_ids(list(existing.keys()))
        generator = impl._generator_matrix_constants

        changes = _MatrixChanges()

        for bc in constraints:
            old = existing.get(bc.id)
            if old is None:
                continue  # new constraint caller handles initial matrix creation

            time_step_changed = bc.time_step != old.time_step
            operator_changed = study_version >= STUDY_VERSION_8_7 and bc.operator != old.operator

            if operator_changed and not time_step_changed:
                # Copy the existing matrix ID into newly required types; delete removed types.
                old_matrix_types = [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[old.operator]]
                new_matrix_types = [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[bc.operator]]
                matrix_type_to_add = [s for s in new_matrix_types if s not in old_matrix_types]
                matrix_type_to_delete = [s for s in old_matrix_types if s not in new_matrix_types]

                if matrix_type_to_add:
                    # For BOTH, lt is the canonical source (mirrors file DAO rename logic).
                    # For single operators, there is only one matrix type so it is unambiguous.
                    source_type = (
                        _MatrixType.LT if old.operator == BindingConstraintOperator.BOTH else old_matrix_types[0]
                    )
                    source_mid = existing_matrix_ids.get(bc.id, {}).get(source_type.value)
                    # The command layer always initializes matrices on creation, so missing source = data corruption.
                    if source_mid is None:
                        raise ValueError(
                            f"Missing source matrix '{source_type.value}' for constraint '{bc.id}' during operator change"
                        )
                    for matrix_type in matrix_type_to_add:
                        changes.add_insertion(bc.id, matrix_type, source_mid)

                for matrix_type in matrix_type_to_delete:
                    changes.add_deletion(bc.id, matrix_type)

            if time_step_changed:
                # Replace all matrices with the null matrix; the simulator uses correctly-sized zeros at runtime.
                null_mid = generator.get_null_matrix()
                if study_version < STUDY_VERSION_8_7:
                    changes.add_deletion(bc.id, _MatrixType.VALUES)
                    changes.add_insertion(bc.id, _MatrixType.VALUES, null_mid)
                else:
                    for matrix_type in [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[old.operator]]:
                        changes.add_deletion(bc.id, matrix_type)
                    for matrix_type in [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[bc.operator]]:
                        changes.add_insertion(bc.id, matrix_type, null_mid)

        return changes

    def _apply_matrix_changes(self, changes: _MatrixChanges) -> None:
        # Apply deletes first, then inserts, within the same transaction.
        db = self._db_session

        # Group deletions by type so we can issue one DELETE … IN (…) per table.
        deletions_by_type: dict[_MatrixType, list[str]] = {}
        for d in changes.deletions:
            deletions_by_type.setdefault(d.suffix, []).append(d.constraint_id)

        for matrice_type, constraint_ids in deletions_by_type.items():
            table = _MATRIX_TYPE_TABLES[matrice_type]
            db.execute(
                delete(table).where((table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids)))
            )

        # Group insertions by type so we can issue one upsert batch per table.
        insertions_by_type: dict[_MatrixType, list[_MatrixInsertion]] = {}
        for ins in changes.insertions:
            insertions_by_type.setdefault(ins.suffix, []).append(ins)

        for matrice_type, insertions in insertions_by_type.items():
            upsert_multiple(
                db,
                _MATRIX_TYPE_TABLES[matrice_type],
                [
                    {"study_id": self._study_id, "constraint_id": ins.constraint_id, "matrix_id": ins.matrix_id}
                    for ins in insertions
                ],
            )

    def _cleanup_scenario_builder_groups(self) -> None:
        """Delete scenario-builder entries for groups no longer referenced by any constraint.

        Must be called after the binding_constraints table already reflects the final state
        (i.e. after upserts in save_constraints, or after deletes in delete_constraints).
        """
        if self.get_impl().get_version() < STUDY_VERSION_8_7:
            return
        # COALESCE handles the case where group IS NULL in DB, which maps to "default".
        active_groups = (
            select(func.coalesce(BC.c.group, DEFAULT_GROUP)).where(BC.c.study_id == self._study_id).distinct()
        )
        self._db_session.execute(
            delete(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == self._study_id)
                & SCENARIO_BINDING_CONSTRAINTS_TABLE.c.bc_group_id.not_in(active_groups)
            )
        )

    def _bc_to_row(self, study_id: str, bc: BindingConstraint) -> dict[str, Any]:
        data = bc.model_dump(exclude={"id", "terms"})
        return {"study_id": study_id, "constraint_id": bc.id, **data}

    def _cluster_term_to_row(self, study_id: str, constraint_id: str, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, ClusterTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            **term.model_dump(exclude={"data"}),
            **term.data.model_dump(),
        }

    def _link_term_to_row(self, study_id: str, constraint_id: str, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, LinkTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            **term.model_dump(exclude={"data"}),
            **term.data.model_dump(),
        }

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_VALUES_MATRIX_TABLE, [(constraint_id, series_id)])
        self._db_session.commit()

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_LT_MATRIX_TABLE, [(constraint_id, series_id)])
        self._db_session.commit()

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_GT_MATRIX_TABLE, [(constraint_id, series_id)])
        self._db_session.commit()

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_EQ_MATRIX_TABLE, [(constraint_id, series_id)])
        self._db_session.commit()

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        db = self._db_session
        constraint_ids = {bc.id for bc in constraints}

        # Delete BC rows first so the table reflects the final state,
        # then prune orphaned groups via a single subquery.
        db.execute(delete(BC).where((BC.c.study_id == self._study_id) & (BC.c.constraint_id.in_(constraint_ids))))
        self._cleanup_scenario_builder_groups()

        db.commit()
