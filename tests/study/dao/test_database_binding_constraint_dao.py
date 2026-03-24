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

import polars as pl
import pytest
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.business.model.common import FilterOption
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.binding_constraint import (
    BINDING_CONSTRAINT_CLUSTER_TERM_TABLE,
    BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
    BINDING_CONSTRAINT_GT_MATRIX_TABLE,
    BINDING_CONSTRAINT_LINK_TERM_TABLE,
    BINDING_CONSTRAINT_LT_MATRIX_TABLE,
    BINDING_CONSTRAINT_TABLE,
    BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
)
from antarest.study.model import STUDY_VERSION_8_8, Study
from tests.study.dao.conftest import build_db_dao


def _assert_tables_empty(db_session: Session, tables: list[Table], study_id: str) -> None:
    for table in tables:
        rows = db_session.execute(select(table).where(table.c.study_id == study_id)).fetchall()
        assert rows == [], f"{table.name}: expected no rows for study {study_id}, found {len(rows)}"


def _bc(constraint_id: str, **kwargs) -> BindingConstraint:
    return BindingConstraint(
        id=constraint_id,
        name=kwargs.pop("name", constraint_id),
        enabled=kwargs.pop("enabled", True),
        time_step=kwargs.pop("time_step", BindingConstraintFrequency.HOURLY),
        operator=kwargs.pop("operator", BindingConstraintOperator.LESS),
        comments=kwargs.pop("comments", ""),
        **kwargs,
    )


def test_constraint_crud(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """Full CRUD lifecycle: empty → save → get → update → delete → study isolation."""
    # Initially empty
    assert db_dao.get_all_constraints() == {}
    with pytest.raises(BindingConstraintNotFound):
        db_dao.get_constraint("ghost")

    # Save two constraints and read them back
    c1 = _bc(
        "c1",
        name="C1",
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.GREATER,
        comments="my comment",
    )
    c2 = _bc(
        "c2",
        name="C2",
        enabled=False,
        time_step=BindingConstraintFrequency.WEEKLY,
        operator=BindingConstraintOperator.BOTH,
        comments="x",
    )
    db_dao.save_constraints([c1, c2])

    result = db_dao.get_all_constraints()
    assert set(result.keys()) == {"c1", "c2"}
    r1 = db_dao.get_constraint("c1")
    assert r1.name == "C1" and r1.time_step == BindingConstraintFrequency.DAILY and r1.comments == "my comment"
    r2 = result["c2"]
    assert r2.enabled is False and r2.operator == BindingConstraintOperator.BOTH

    # Update c2 (upsert)
    c2_updated = _bc(
        "c2",
        name="C2",
        enabled=False,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.EQUAL,
        comments="new comment",
    )
    db_dao.save_constraints([c1, c2_updated])
    r2 = db_dao.get_constraint("c2")
    assert r2.time_step == BindingConstraintFrequency.HOURLY
    assert r2.operator == BindingConstraintOperator.EQUAL
    assert r2.comments == "new comment"

    # Save only c1 → c2 is removed
    db_dao.save_constraints([c1])
    assert set(db_dao.get_all_constraints().keys()) == {"c1"}

    # Explicit delete
    db_dao.save_constraints([c1, c2_updated])
    assert set(db_dao.get_all_constraints().keys()) == {"c1", "c2"}
    db_dao.delete_constraints([c1])
    assert "c1" not in db_dao.get_all_constraints()
    assert "c2" in db_dao.get_all_constraints()

    # Deleting a nonexistent constraint is a noop
    db_dao.delete_constraints([_bc("ghost")])

    # Constraints are isolated per study
    dao2 = build_db_dao(db_session, db_dao._matrix_service, STUDY_VERSION_8_8)
    assert dao2.get_all_constraints() == {}


def test_constraint_terms(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """Terms lifecycle: save link/cluster/mixed, no terms, term replacement, cartesian-product regression."""
    # Link term
    db_dao.save_constraints(
        [_bc("lc", terms=[ConstraintTerm(weight=3.5, data=LinkTerm(area1="area_a", area2="area_b"))])]
    )
    r = db_dao.get_constraint("lc")
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, LinkTerm) and t.weight == 3.5 and t.offset is None
    assert {t.data.area1, t.data.area2} == {"area_a", "area_b"}

    # Cluster term
    db_dao.save_constraints(
        [_bc("cc", terms=[ConstraintTerm(weight=4.0, offset=2, data=ClusterTerm(area="area_a", cluster="cl1"))])]
    )
    r = db_dao.get_constraint("cc")
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, ClusterTerm) and t.data.area == "area_a" and t.data.cluster == "cl1"
    assert t.weight == 4.0 and t.offset == 2

    # Mixed terms
    db_dao.save_constraints(
        [
            _bc(
                "mixed",
                terms=[
                    ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
                    ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="a", cluster="c1")),
                ],
            )
        ]
    )
    r = db_dao.get_constraint("mixed")
    assert len(r.terms) == 2
    assert {type(t.data) for t in r.terms} == {LinkTerm, ClusterTerm}

    # No terms
    db_dao.save_constraints([_bc("empty", terms=[])])
    assert db_dao.get_constraint("empty").terms == []

    # Cartesian product regression: 2 link + 1 cluster must yield exactly 3 terms
    db_dao.save_constraints(
        [
            _bc(
                "bc_cart",
                terms=[
                    ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
                    ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),
                    ConstraintTerm(weight=3.0, data=ClusterTerm(area="x", cluster="y")),
                ],
            )
        ]
    )
    r = db_dao.get_constraint("bc_cart")
    assert len(r.terms) == 3
    assert len([t for t in r.terms if isinstance(t.data, LinkTerm)]) == 2
    assert len([t for t in r.terms if isinstance(t.data, ClusterTerm)]) == 1

    # Term replacement scenario: A B C → B C' (A removed, C updated, sibling bc2 untouched)
    bc1_v1 = _bc(
        "bc1",
        terms=[
            ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),  # A – will be removed
            ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),  # B – kept
            ConstraintTerm(weight=3.0, offset=1, data=ClusterTerm(area="x", cluster="y")),  # C – weight updated
        ],
    )
    bc2 = _bc("bc2", terms=[ConstraintTerm(weight=5.0, data=ClusterTerm(area="p", cluster="q"))])
    db_dao.save_constraints([bc1_v1, bc2])
    assert len(db_dao.get_constraint("bc1").terms) == 3

    bc1_v2 = _bc(
        "bc1",
        terms=[
            ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),  # B unchanged
            ConstraintTerm(weight=99.0, offset=1, data=ClusterTerm(area="x", cluster="y")),  # C' updated weight
        ],
    )
    db_dao.save_constraints([bc1_v2, bc2])

    r = db_dao.get_constraint("bc1")
    assert len(r.terms) == 2
    cluster_terms = [t for t in r.terms if isinstance(t.data, ClusterTerm)]
    assert cluster_terms[0].weight == 99.0

    # bc2 must be untouched throughout
    assert db_dao.get_constraint("bc2").terms[0].weight == 5.0


def test_version_specific_fields(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """filter_year_by_year, filter_synthesis and group round-trip correctly; nullables stay None."""
    # Filter fields and group
    db_dao.save_constraints(
        [
            _bc(
                "bc1",
                filter_year_by_year=[FilterOption.HOURLY, FilterOption.DAILY],
                filter_synthesis=[FilterOption.WEEKLY],
                group="my_group",
            )
        ]
    )
    r = db_dao.get_constraint("bc1")
    assert FilterOption.HOURLY in r.filter_year_by_year
    assert FilterOption.DAILY in r.filter_year_by_year
    assert r.filter_synthesis == [FilterOption.WEEKLY]
    assert r.group == "my_group"

    # Filter fields must be stored as comma-separated strings, not raw list reprs
    with db_session:
        row = db_session.execute(
            select(
                BINDING_CONSTRAINT_TABLE.c.filter_year_by_year,
                BINDING_CONSTRAINT_TABLE.c.filter_synthesis,
            ).where(BINDING_CONSTRAINT_TABLE.c.constraint_id == "bc1")
        ).fetchone()
    assert isinstance(row.filter_year_by_year, str), f"Expected str, got {type(row.filter_year_by_year)}"
    assert "hourly" in row.filter_year_by_year and "daily" in row.filter_year_by_year
    assert "[" not in row.filter_year_by_year, "Raw list repr was stored instead of a string"
    assert "weekly" in row.filter_synthesis

    # Nullable fields round-trip as None
    db_dao.save_constraints([_bc("bc2", filter_year_by_year=None, filter_synthesis=None, group=None)])
    r2 = db_dao.get_constraint("bc2")
    assert r2.filter_year_by_year is None
    assert r2.filter_synthesis is None
    assert r2.group is None


def test_matrices(db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService]) -> None:
    """All four matrix types round-trip; upsert overwrites; each constraint has its own matrices."""
    db_dao, matrix_service = db_dao_930_and_matrix_service

    df_v = pl.DataFrame({"v": [1.0, 2.0]})
    df_lt = pl.DataFrame({"lt": [0.5, 1.5]})
    df_gt = pl.DataFrame({"gt": [2.0, 3.0]})
    df_eq = pl.DataFrame({"eq": [7.0]})
    df_new = pl.DataFrame({"v": [99.0]})

    db_dao.save_constraints(
        [
            _bc("bc1", operator=BindingConstraintOperator.LESS),
            _bc("bc2", operator=BindingConstraintOperator.GREATER),
        ]
    )

    # All four types
    db_dao.save_constraint_values_matrix("bc1", matrix_service.create(df_v))
    db_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_lt))
    db_dao.save_constraint_greater_term_matrix("bc2", matrix_service.create(df_gt))
    db_dao.save_constraint_equal_term_matrix("bc1", matrix_service.create(df_eq))

    assert db_dao.get_constraint_values_matrix("bc1").equals(df_v)
    assert db_dao.get_constraint_less_term_matrix("bc1").equals(df_lt)
    assert db_dao.get_constraint_greater_term_matrix("bc2").equals(df_gt)
    assert db_dao.get_constraint_equal_term_matrix("bc1").equals(df_eq)

    # Upsert: saving the same matrix type twice overwrites
    db_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_new))
    assert db_dao.get_constraint_less_term_matrix("bc1").equals(df_new)

    # Each constraint has its own independent matrices
    df_a = pl.DataFrame({"a": [1.0]})
    df_b = pl.DataFrame({"b": [2.0]})
    db_dao.save_constraints([_bc("bc_a"), _bc("bc_b")])
    db_dao.save_constraint_less_term_matrix("bc_a", matrix_service.create(df_a))
    db_dao.save_constraint_less_term_matrix("bc_b", matrix_service.create(df_b))
    assert db_dao.get_constraint_less_term_matrix("bc_a").equals(df_a)
    assert db_dao.get_constraint_less_term_matrix("bc_b").equals(df_b)


def test_cascade_deletes(
    db_session: Session,
    db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService],
) -> None:
    """Deleting a constraint or its study cascades to all child tables."""
    db_dao, matrix_service = db_dao_930_and_matrix_service
    study_id = db_dao.get_study_id()
    series_id = matrix_service.create(pl.DataFrame({"v": [1.0]}))

    constraint = _bc(
        "bc1",
        terms=[
            ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
            ConstraintTerm(weight=2.0, data=ClusterTerm(area="a", cluster="c1")),
        ],
    )
    db_dao.save_constraints([constraint])
    db_dao.save_constraint_values_matrix("bc1", series_id)
    db_dao.save_constraint_less_term_matrix("bc1", series_id)
    db_dao.save_constraint_greater_term_matrix("bc1", series_id)
    db_dao.save_constraint_equal_term_matrix("bc1", series_id)

    # Delete constraint → all child rows gone
    db_dao.delete_constraints([constraint])
    with db_session:
        _assert_tables_empty(
            db_session,
            [
                BINDING_CONSTRAINT_LINK_TERM_TABLE,
                BINDING_CONSTRAINT_CLUSTER_TERM_TABLE,
                BINDING_CONSTRAINT_VALUES_MATRIX_TABLE,
                BINDING_CONSTRAINT_LT_MATRIX_TABLE,
                BINDING_CONSTRAINT_GT_MATRIX_TABLE,
                BINDING_CONSTRAINT_EQ_MATRIX_TABLE,
            ],
            study_id,
        )

    # Delete study row → DB-level cascade removes everything
    db_dao.save_constraints([_bc("bc2", terms=[ConstraintTerm(weight=1.0, data=LinkTerm(area1="x", area2="y"))])])
    db_dao.save_constraint_less_term_matrix("bc2", series_id)

    with db_session:
        study = db_session.get(Study, study_id)
        db_session.delete(study)
        db_session.commit()

    with db_session:
        _assert_tables_empty(
            db_session,
            [
                BINDING_CONSTRAINT_TABLE,
                BINDING_CONSTRAINT_LINK_TERM_TABLE,
                BINDING_CONSTRAINT_LT_MATRIX_TABLE,
            ],
            study_id,
        )
