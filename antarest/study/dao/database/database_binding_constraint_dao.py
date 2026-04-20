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
from typing import TYPE_CHECKING, Any, NewType, Sequence

import polars as pl
from antares.study.version import StudyVersion
from sqlalchemy import Row, Table, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, join
from sqlalchemy.sql import outerjoin
from typing_extensions import override

from antarest.core.exceptions import BindingConstraintNotFound, BindingConstraintsNotFound
from antarest.study.business.model.binding_constraint_model import (
    OPERATOR_MATRICES_MAP,
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintId,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao
from antarest.study.dao.common import BindingConstraintSeriesMapping, SeriesId
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
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)

DEFAULT_MATRICES_AFTER_V87 = {
    BindingConstraintFrequency.HOURLY: default_bc_hourly_87,
    BindingConstraintFrequency.DAILY: default_bc_weekly_daily_87,
    BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_87,
}

DEFAULT_MATRICES_BEFORE_V87 = {
    BindingConstraintFrequency.HOURLY: default_bc_hourly_86,
    BindingConstraintFrequency.DAILY: default_bc_weekly_daily_86,
    BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_86,
}


class _MatrixType(str, Enum):
    LT = "lt"
    GT = "gt"
    EQ = "eq"
    VALUES = "values"


_MatrixID = NewType("_MatrixID", str)

# Maps constraint_id → (matrix_type → matrix_id)
_MatrixIdsByConstraint = dict[ConstraintId, dict["_MatrixType", _MatrixID]]

_MATRIX_TYPE_TABLES: dict["_MatrixType", Table] = {
    _MatrixType.LT: BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    _MatrixType.GT: BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    _MatrixType.EQ: BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    _MatrixType.VALUES: BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
}


@dataclass
class _MatrixDeletion:
    """Identifies a matrix row to remove: delete the <type> row for <constraint_id>."""

    constraint_id: ConstraintId
    matrix_type: _MatrixType


@dataclass
class _MatrixInsertion:
    """Identifies a matrix row to create or overwrite: write <matrix_id> into the <type> table for <constraint_id>."""

    constraint_id: ConstraintId
    matrix_type: _MatrixType
    matrix_id: _MatrixID


@dataclass
class _MatrixChanges:
    """Accumulates matrix-table changes for a batch of constraint updates."""

    deletions: list[_MatrixDeletion] = field(default_factory=list)
    insertions: list[_MatrixInsertion] = field(default_factory=list)

    def add_deletion(self, constraint_id: ConstraintId, matrix_type: _MatrixType) -> None:
        self.deletions.append(_MatrixDeletion(constraint_id, matrix_type))

    def add_insertion(self, constraint_id: ConstraintId, matrix_type: _MatrixType, matrix_id: _MatrixID) -> None:
        self.insertions.append(_MatrixInsertion(constraint_id, matrix_type, matrix_id))


if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseBindingConstraintDao(ConstraintDao):
    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

    def _fetch_constraints(self, constraint_ids: list[ConstraintId]) -> dict[ConstraintId, BindingConstraint]:
        """
        Two steps in this function
        Step 1 : BC LEFT JOIN link_terms builds the result dict: one entry per constraint, pre-populated with
        its BC fields and link terms.
        Step 2 : SELECT cluster_terms fetches cluster_terms and appends them.

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
        if constraint_ids:
            q1 = q1.where(BC.c.constraint_id.in_(constraint_ids))

        bc_rows: dict[ConstraintId, Any] = {}
        terms: dict[ConstraintId, list[ConstraintTerm]] = {}

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
        if constraint_ids:
            ct_filter = ct_filter & (CT.c.constraint_id.in_(constraint_ids))

        for row in db.execute(select(CT).where(ct_filter)).fetchall():
            terms[row.constraint_id].append(
                ConstraintTerm(
                    weight=row.weight, offset=row.offset, data=ClusterTerm(area=row.area, cluster=row.cluster)
                )
            )

        return {ConstraintId(cid): self._row_to_bc(bc_rows[cid], terms[cid]) for cid in bc_rows}

    @staticmethod
    def _row_to_bc(row: Row[Any], terms: list[ConstraintTerm]) -> BindingConstraint:
        d = get_row_representation_as_dict(row)
        d["id"] = d.pop("constraint_id")
        d["terms"] = terms
        # extra="allow" is required because the join query returns columns that are
        # not fields of BindingConstraint (such as `area1` or `lt_weight`).
        return BindingConstraint.model_validate(d, extra="allow")

    @override
    def get_all_constraints(self) -> dict[ConstraintId, BindingConstraint]:
        return self._fetch_constraints([])

    @override
    def get_constraint(self, constraint_id: ConstraintId) -> BindingConstraint:
        result = self._fetch_constraints([constraint_id])
        if not result:
            raise BindingConstraintNotFound(f"Constraint {constraint_id} not found")
        return result[constraint_id]

    def _get_bc_matrix_and_frequency(
        self, constraint_id: ConstraintId, table: Table
    ) -> tuple[SeriesId, BindingConstraintFrequency]:
        """
        We need to fetch a constraint frequency to know the default matrix to use.
        We want to avoid fetching terms as we do not need them.
        That's why we use a specific DB request
        """
        join_query = join(
            BC,
            table,
            (BC.c.study_id == table.c.study_id) & (BC.c.constraint_id == table.c.constraint_id == constraint_id),
        )
        q = select(BC.c.time_step, table.c.matrix_id).select_from(join_query)
        row = self._db_session.execute(q).fetchone()
        if row is None:
            raise BindingConstraintNotFound(f"Matrix for constraint {constraint_id} not found")
        return str(row.matrix_id), row.time_step

    def _raise_the_right_binding_constraint_exception(
        self, bc_ids: set[str], exc: IntegrityError | None = None
    ) -> None:
        # Checks if some binding constraints do not exist
        all_constraints = set(self.get_all_constraints())
        if invalid_bcs := bc_ids - all_constraints:
            if len(invalid_bcs) == 1:
                raise BindingConstraintNotFound(next(iter(invalid_bcs))) from exc
            raise BindingConstraintsNotFound(*invalid_bcs) from exc

        # All constraints exist. It means that the DB table does not contain the information.
        raise ValueError("One of the binding constraints table is not filled as it should") from exc

    def _save_bc_matrices(self, table: Table, series: BindingConstraintSeriesMapping) -> None:
        rows = [{"study_id": self._study_id, "constraint_id": cid, "matrix_id": mid} for cid, mid in series.items()]

        try:
            upsert_multiple(self._db_session, table, rows)
        except IntegrityError as e:
            self._raise_the_right_binding_constraint_exception(set(series), e)

    @override
    def get_constraint_values_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        matrix_id, frequency = self._get_bc_matrix_and_frequency(constraint_id, BINDING_CONSTRAINT_VALUES_MATRIX_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=DEFAULT_MATRICES_BEFORE_V87[frequency])

    @override
    def get_constraint_less_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        matrix_id, frequency = self._get_bc_matrix_and_frequency(constraint_id, BINDING_CONSTRAINT_LT_MATRIX_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=DEFAULT_MATRICES_AFTER_V87[frequency])

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        matrix_id, frequency = self._get_bc_matrix_and_frequency(constraint_id, BINDING_CONSTRAINT_GT_MATRIX_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=DEFAULT_MATRICES_AFTER_V87[frequency])

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        matrix_id, frequency = self._get_bc_matrix_and_frequency(constraint_id, BINDING_CONSTRAINT_EQ_MATRIX_TABLE)
        return self.get_impl().get_matrix(matrix_id, default_empty_supplier=DEFAULT_MATRICES_AFTER_V87[frequency])

    @override
    def get_all_constraint_values_matrix(self) -> BindingConstraintSeriesMapping:
        return self.get_all_bc_matrices(BINDING_CONSTRAINT_VALUES_MATRIX_TABLE)

    @override
    def get_all_constraint_less_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self.get_all_bc_matrices(BINDING_CONSTRAINT_LT_MATRIX_TABLE)

    @override
    def get_all_constraint_greater_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self.get_all_bc_matrices(BINDING_CONSTRAINT_GT_MATRIX_TABLE)

    @override
    def get_all_constraint_equal_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self.get_all_bc_matrices(BINDING_CONSTRAINT_EQ_MATRIX_TABLE)

    def get_all_bc_matrices(self, table: Table) -> BindingConstraintSeriesMapping:
        study_id = self._study_id
        session = self._db_session
        stmt = select(table).where((table.c.study_id == study_id))
        rows = session.execute(stmt).fetchall()
        return {row.constraint_id: row.matrix_id for row in rows}

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        if not constraints:
            return  # avoid making unnecessary database calls
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
        self._db_session.execute(
            delete(CT).where((CT.c.study_id == self._study_id) & (CT.c.constraint_id.in_(constraint_ids)))
        )
        if cluster_terms:
            upsert_multiple(self._db_session, CT, cluster_terms)

    def _save_link_terms(self, constraints: Sequence[BindingConstraint]) -> None:
        constraint_ids = [bc.id for bc in constraints]
        link_terms = [
            self._link_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, LinkTerm)
        ]
        self._db_session.execute(
            delete(LT).where((LT.c.study_id == self._study_id) & (LT.c.constraint_id.in_(constraint_ids)))
        )
        if link_terms:
            upsert_multiple(self._db_session, LT, link_terms)

    def _fetch_existing_matrix_ids(self, constraint_ids: list[ConstraintId]) -> _MatrixIdsByConstraint:
        """Fetch all existing matrix IDs upfront needed for operator change (copy source)."""
        existing_matrix_ids: _MatrixIdsByConstraint = {}
        for matrix_type, table in _MATRIX_TYPE_TABLES.items():
            rows = self._db_session.execute(
                select(table.c.constraint_id, table.c.matrix_id).where(
                    (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids))
                )
            ).fetchall()
            for row in rows:
                existing_matrix_ids.setdefault(ConstraintId(row.constraint_id), {})[matrix_type] = _MatrixID(
                    row.matrix_id
                )
        return existing_matrix_ids

    def _handle_time_step_change(
        self,
        changes: _MatrixChanges,
        bc: BindingConstraint,
        old: BindingConstraint,
        study_version: StudyVersion,
        null_mid: _MatrixID,
    ) -> None:
        """Replace all existing matrix rows with the null matrix.

        The matrix row count is tied to the time-step frequency
        (hourly=8784 rows, daily/weekly=366 rows), so existing data would be
        the wrong shape after a time-step change. The simulator fills in
        correctly-sized zeros at runtime from the null matrix.
        """
        if study_version < STUDY_VERSION_8_7:
            changes.add_deletion(bc.id, _MatrixType.VALUES)
            changes.add_insertion(bc.id, _MatrixType.VALUES, null_mid)
        else:
            for matrix_type in [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[old.operator]]:
                changes.add_deletion(bc.id, matrix_type)
            for matrix_type in [_MatrixType(t) for t in OPERATOR_MATRICES_MAP[bc.operator]]:
                changes.add_insertion(bc.id, matrix_type, null_mid)

    @staticmethod
    def _get_source_matrix_id(
        existing_matrix_ids: _MatrixIdsByConstraint, operator: BindingConstraintOperator, constraint_id: ConstraintId
    ) -> _MatrixID:
        """Return the canonical source matrix ID for the given operator.

        A missing entry means the DB is corrupted: the command layer always initialises
        all required matrices at creation time.
        """
        match operator:
            case BindingConstraintOperator.GREATER:
                source_type = _MatrixType.GT
            case BindingConstraintOperator.EQUAL:
                source_type = _MatrixType.EQ
            case _:  # LESS or BOTH → lt
                source_type = _MatrixType.LT
        mid = existing_matrix_ids.get(constraint_id, {}).get(source_type)
        if mid is None:
            raise ValueError(
                f"Data corruption: matrix '{source_type.value}' is missing for constraint '{constraint_id}'. "
                "All matrices should have been initialised at creation time."
            )
        return mid

    @staticmethod
    def _handle_operator_change(
        changes: _MatrixChanges,
        bc: BindingConstraint,
        old: BindingConstraint,
        existing_matrix_ids: _MatrixIdsByConstraint,
    ) -> None:
        """Reroute existing matrix IDs to match the new operator's matrix types.

        Each operator owns a specific set of matrix types (lt, gt, eq).
        Existing matrix IDs are copied into newly required tables and removed
        from tables that are no longer needed, so user data is preserved rather
        than reset.

        The canonical source matrix is the first (and only) matrix of the old operator.
        For BOTH, lt is canonical (used when collapsing to a single-operator type).
        A missing entry means the DB is corrupted: the command layer always initialises
        all required matrices at creation time.
        """
        source_mid = DatabaseBindingConstraintDao._get_source_matrix_id(existing_matrix_ids, old.operator, bc.id)

        def deletion(t: _MatrixType) -> None:
            changes.add_deletion(bc.id, t)

        def insertion(t: _MatrixType) -> None:
            changes.add_insertion(bc.id, t, source_mid)

        lt_matrice = _MatrixType.LT
        gt_matrice = _MatrixType.GT
        eq_matrice = _MatrixType.EQ

        OP = BindingConstraintOperator
        match (old.operator, bc.operator):
            # LESS
            case (OP.LESS, OP.GREATER):
                deletion(lt_matrice)
                insertion(gt_matrice)
            case (OP.LESS, OP.EQUAL):
                deletion(lt_matrice)
                insertion(eq_matrice)
            case (OP.LESS, OP.BOTH):
                insertion(gt_matrice)

            # GREATER
            case (OP.GREATER, OP.LESS):
                deletion(gt_matrice)
                insertion(lt_matrice)
            case (OP.GREATER, OP.EQUAL):
                deletion(gt_matrice)
                insertion(eq_matrice)
            case (OP.GREATER, OP.BOTH):
                insertion(lt_matrice)

            # EQUAL
            case (OP.EQUAL, OP.LESS):
                deletion(eq_matrice)
                insertion(lt_matrice)
            case (OP.EQUAL, OP.GREATER):
                deletion(eq_matrice)
                insertion(gt_matrice)
            case (OP.EQUAL, OP.BOTH):
                deletion(eq_matrice)
                insertion(lt_matrice)
                insertion(gt_matrice)

            # BOTH
            case (OP.BOTH, OP.LESS):
                deletion(gt_matrice)
            case (OP.BOTH, OP.GREATER):
                deletion(lt_matrice)
            case (OP.BOTH, OP.EQUAL):
                deletion(lt_matrice)
                deletion(gt_matrice)
                insertion(eq_matrice)

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
        constraint_ids = [bc.id for bc in constraints]
        # Fetch only the constraints being updated, not the entire study.
        existing = self._fetch_constraints(constraint_ids=constraint_ids)
        null_matrix_id = _MatrixID(impl.generator_matrix_constants.get_null_matrix())
        changes = _MatrixChanges()

        time_step_changed = []
        operator_changed = []
        for bc in constraints:
            old = existing.get(bc.id)
            if old is None:
                continue  # new constraint, caller handles initial matrix creation

            if bc.time_step != old.time_step:
                time_step_changed.append((old, bc))
            elif study_version >= STUDY_VERSION_8_7 and bc.operator != old.operator:
                operator_changed.append((old, bc))

        # avoid doing unnecessary work if no operator changed
        if operator_changed:
            existing_matrix_ids = self._fetch_existing_matrix_ids(constraint_ids)

        for old, bc in time_step_changed:
            self._handle_time_step_change(changes, bc, old, study_version, null_matrix_id)
        for old, bc in operator_changed:
            self._handle_operator_change(changes, bc, old, existing_matrix_ids)

        return changes

    def _apply_matrix_changes(self, changes: _MatrixChanges) -> None:
        # Apply deletes first, then inserts, within the same transaction.
        db = self._db_session

        # Group deletions by type so we can issue one DELETE … IN (…) per table.
        deletions_by_type: dict[_MatrixType, list[str]] = {}
        for d in changes.deletions:
            deletions_by_type.setdefault(d.matrix_type, []).append(d.constraint_id)

        for matrix_type, constraint_ids in deletions_by_type.items():
            table = _MATRIX_TYPE_TABLES[matrix_type]
            db.execute(
                delete(table).where((table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids)))
            )

        # Group insertions by type so we can issue one upsert batch per table.
        insertions_by_type: dict[_MatrixType, list[_MatrixInsertion]] = {}
        for ins in changes.insertions:
            insertions_by_type.setdefault(ins.matrix_type, []).append(ins)

        for matrix_type, insertions in insertions_by_type.items():
            upsert_multiple(
                db,
                _MATRIX_TYPE_TABLES[matrix_type],
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
        active_groups = select(BC.c.group).where(BC.c.study_id == self._study_id).distinct()
        self._db_session.execute(
            delete(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == self._study_id)
                & SCENARIO_BINDING_CONSTRAINTS_TABLE.c.bc_group_id.not_in(active_groups)
            )
        )

    def _bc_to_row(self, study_id: str, bc: BindingConstraint) -> dict[str, Any]:
        data = bc.model_dump(exclude={"id", "terms"})
        return {"study_id": study_id, "constraint_id": bc.id, **data}

    def _cluster_term_to_row(self, study_id: str, constraint_id: ConstraintId, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, ClusterTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            **term.model_dump(exclude={"data"}),
            **term.data.model_dump(),
        }

    def _link_term_to_row(self, study_id: str, constraint_id: ConstraintId, term: ConstraintTerm) -> dict[str, Any]:
        assert isinstance(term.data, LinkTerm)
        return {
            "study_id": study_id,
            "constraint_id": constraint_id,
            **term.model_dump(exclude={"data"}),
            **term.data.model_dump(),
        }

    @override
    def save_constraint_values_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_VALUES_MATRIX_TABLE, series)
        self._db_session.commit()

    @override
    def save_constraint_less_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_LT_MATRIX_TABLE, series)
        self._db_session.commit()

    @override
    def save_constraint_greater_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_GT_MATRIX_TABLE, series)
        self._db_session.commit()

    @override
    def save_constraint_equal_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self._save_bc_matrices(BINDING_CONSTRAINT_EQ_MATRIX_TABLE, series)
        self._db_session.commit()

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        """
        Delete binding constraints and their associated matrix rows from the database.

        Deleting a constraint not present in the study is a no-op.
        """
        db = self._db_session
        constraint_ids = {bc.id for bc in constraints}

        # Order matters : delete BC rows first so the table reflects the final state,
        # then prune orphaned groups via a single subquery.
        db.execute(delete(BC).where((BC.c.study_id == self._study_id) & (BC.c.constraint_id.in_(constraint_ids))))
        self._cleanup_scenario_builder_groups()

        db.commit()
