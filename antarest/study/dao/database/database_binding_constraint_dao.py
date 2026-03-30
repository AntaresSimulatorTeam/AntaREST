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
from antares.study.version import StudyVersion
from sqlalchemy import Table, delete, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import outerjoin
from typing_extensions import override

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.matrixstore.service import MATRIX_PROTOCOL_PREFIX
from antarest.study.business.model.binding_constraint_model import (
    DEFAULT_GROUP,
    OPERATOR_MATRICES_MAP,
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
    initialize_binding_constraint,
)
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
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants

_TERM_MATRIX_TABLES: dict[str, Table] = {
    "lt": BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    "gt": BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    "eq": BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    "values": BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
}

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

        version = self.get_impl().get_version()
        return {cid: self._row_to_bc(bc_rows[cid], terms[cid], version) for cid in bc_rows}

    @staticmethod
    def _row_to_bc(row: Any, terms: list[ConstraintTerm], version: Any) -> BindingConstraint:
        bc = BindingConstraint(
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
        impl = self.get_impl()
        study_version = impl.get_version()
        constants = impl._generator_matrix_constants

        constraint_ids = [bc.id for bc in constraints]
        # Fetch existing constraints BEFORE upserting (needed for change detection)
        existing = self._fetch_constraints()

        self._save_constraint_rows(constraints)
        self._save_cluster_terms(constraints, constraint_ids)
        self._save_link_terms(constraints, constraint_ids)
        to_delete, to_create = self._compute_matrix_changes(constraints, existing, study_version, constants)
        self._apply_matrix_changes(to_delete, to_create)
        self._cleanup_scenario_builder_groups(constraints, existing)

        self._db_session.commit()

    def _save_constraint_rows(self, constraints: Sequence[BindingConstraint]) -> None:
        upsert_multiple(
            self._db_session,
            BINDING_CONSTRAINT_TABLE,
            [self._bc_to_row(self._study_id, bc) for bc in constraints],
        )

    def _save_cluster_terms(self, constraints: Sequence[BindingConstraint], constraint_ids: list[str]) -> None:
        cluster_terms = [
            self._cluster_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, ClusterTerm)
        ]
        self._db_session.execute(
            delete(BINDING_CONSTRAINT_CLUSTER_TERM_TABLE).where(
                (BINDING_CONSTRAINT_CLUSTER_TERM_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_CLUSTER_TERM_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )
        upsert_multiple(self._db_session, BINDING_CONSTRAINT_CLUSTER_TERM_TABLE, cluster_terms)

    def _save_link_terms(self, constraints: Sequence[BindingConstraint], constraint_ids: list[str]) -> None:
        link_terms = [
            self._link_term_to_row(self._study_id, bc.id, term)
            for bc in constraints
            for term in bc.terms
            if isinstance(term.data, LinkTerm)
        ]
        self._db_session.execute(
            delete(BINDING_CONSTRAINT_LINK_TERM_TABLE).where(
                (BINDING_CONSTRAINT_LINK_TERM_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_LINK_TERM_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )
        upsert_multiple(self._db_session, BINDING_CONSTRAINT_LINK_TERM_TABLE, link_terms)

    def _fetch_existing_matrix_ids(self, constraint_ids: list[str]) -> dict[str, dict[str, str]]:
        """Fetch all existing matrix IDs upfront — needed for operator change (copy source)."""
        existing_matrix_ids: dict[str, dict[str, str]] = {}
        for term, table in _TERM_MATRIX_TABLES.items():
            rows = self._db_session.execute(
                select(table.c.constraint_id, table.c.matrix_id).where(
                    (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(constraint_ids))
                )
            ).fetchall()
            for row in rows:
                existing_matrix_ids.setdefault(row.constraint_id, {})[term] = row.matrix_id
        return existing_matrix_ids

    @staticmethod
    def _default_matrix_id(
        time_step: BindingConstraintFrequency, study_version: StudyVersion, constants: GeneratorMatrixConstants
    ) -> str:
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

    def _compute_matrix_changes(
        self,
        constraints: Sequence[BindingConstraint],
        existing: dict[str, BindingConstraint],
        study_version: StudyVersion,
        constants: GeneratorMatrixConstants,
    ) -> tuple[dict[str, list[str]], dict[str, list[tuple[str, str]]]]:
        constraint_ids = [bc.id for bc in constraints]
        existing_matrix_ids = self._fetch_existing_matrix_ids(constraint_ids)

        to_delete: dict[str, list[str]] = {t: [] for t in _TERM_MATRIX_TABLES}
        to_create: dict[str, list[tuple[str, str]]] = {t: [] for t in _TERM_MATRIX_TABLES}

        for bc in constraints:
            old = existing.get(bc.id)
            if old is None:
                continue  # new constraint — caller handles initial matrix creation

            time_step_changed = bc.time_step != old.time_step
            operator_changed = study_version >= STUDY_VERSION_8_7 and bc.operator != old.operator

            if operator_changed and not time_step_changed:
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
                    # The command layer always initializes matrices on creation, so missing source = data corruption.
                    if source_mid is None:
                        raise ValueError(
                            f"Missing source matrix '{source_term}' for constraint '{bc.id}' during operator change"
                        )
                    for term in terms_to_add:
                        to_create[term].append((bc.id, source_mid))

                for term in terms_to_del:
                    to_delete[term].append(bc.id)

            if time_step_changed:
                # Reset all matrices to zero defaults for the new time step.
                default_mid = self._default_matrix_id(bc.time_step, study_version, constants)
                if study_version < STUDY_VERSION_8_7:
                    to_delete["values"].append(bc.id)
                    to_create["values"].append((bc.id, default_mid))
                else:
                    for term in OPERATOR_MATRICES_MAP[old.operator]:
                        to_delete[term].append(bc.id)
                    for term in OPERATOR_MATRICES_MAP[bc.operator]:
                        to_create[term].append((bc.id, default_mid))

        return to_delete, to_create

    def _apply_matrix_changes(
        self,
        to_delete: dict[str, list[str]],
        to_create: dict[str, list[tuple[str, str]]],
    ) -> None:
        # Apply deletes first, then creates, within the same transaction
        db = self._db_session
        for term, table in _TERM_MATRIX_TABLES.items():
            if to_delete[term]:
                db.execute(
                    delete(table).where(
                        (table.c.study_id == self._study_id) & (table.c.constraint_id.in_(to_delete[term]))
                    )
                )
        for term, table in _TERM_MATRIX_TABLES.items():
            if to_create[term]:
                upsert_multiple(
                    db,
                    table,
                    [
                        {"study_id": self._study_id, "constraint_id": cid, "matrix_id": mid}
                        for cid, mid in to_create[term]
                    ],
                )

    def _cleanup_scenario_builder_groups(
        self,
        constraints: Sequence[BindingConstraint],
        existing: dict[str, BindingConstraint],
    ) -> None:
        version = self.get_impl().get_version()
        saved_ids = {bc.id for bc in constraints}
        groups_before = {bc.group for bc in existing.values() if bc.group}
        groups_after = {bc.group for bc in constraints if bc.group} | {
            bc.group for bc in existing.values() if bc.group and bc.id not in saved_ids
        }
        # For v8.7+, group=None means "default" (NULL in DB reads back as "default" via
        # initialize_binding_constraint). If any saved constraint has group=None, "default"
        # is still in use and must not be removed from the scenario builder.
        if version >= STUDY_VERSION_8_7 and any(bc.group is None for bc in constraints):
            groups_after.add(DEFAULT_GROUP)
        removed_groups = groups_before - groups_after
        if removed_groups:
            self._db_session.execute(
                delete(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                    (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == self._study_id)
                    & (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.bc_group_id.in_(removed_groups))
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

        # Compute orphaned groups before deleting (need the full picture first)
        existing = self._fetch_constraints()
        deleted_groups = {bc.group for bc in constraints if bc.group}
        remaining_groups = {bc.group for bc in existing.values() if bc.group and bc.id not in set(constraint_ids)}
        orphaned_groups = deleted_groups - remaining_groups

        db.execute(
            delete(BINDING_CONSTRAINT_TABLE).where(
                (BINDING_CONSTRAINT_TABLE.c.study_id == self._study_id)
                & (BINDING_CONSTRAINT_TABLE.c.constraint_id.in_(constraint_ids))
            )
        )

        if orphaned_groups:
            db.execute(
                delete(SCENARIO_BINDING_CONSTRAINTS_TABLE).where(
                    (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.study_id == self._study_id)
                    & (SCENARIO_BINDING_CONSTRAINTS_TABLE.c.bc_group_id.in_(orphaned_groups))
                )
            )

        db.commit()
