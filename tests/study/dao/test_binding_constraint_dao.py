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
Binding constraint DAO tests, parameterized across both database and filesystem backends.
"""

import polars as pl
import pytest
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from antarest.core.exceptions import BindingConstraintNotFound, ChildNotFoundError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintId,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.scenario_builder_model import Ruleset
from antarest.study.dao.api.study_dao import StudyDao
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

# Common constraint IDs reused across many tests
BC1: ConstraintId = ConstraintId("bc1")
BC2: ConstraintId = ConstraintId("bc2")
BC3: ConstraintId = ConstraintId("bc3")


def _bc(constraint_id: ConstraintId, **kwargs) -> BindingConstraint:
    return BindingConstraint(
        id=constraint_id,
        name=kwargs.pop("name", constraint_id),
        enabled=kwargs.pop("enabled", True),
        time_step=kwargs.pop("time_step", BindingConstraintFrequency.HOURLY),
        operator=kwargs.pop("operator", BindingConstraintOperator.LESS),
        comments=kwargs.pop("comments", ""),
        **kwargs,
    )


def _missing_matrix_error(dao: StudyDao) -> type[Exception]:
    """Return the exception type raised when reading a nonexistent matrix."""
    return BindingConstraintNotFound if isinstance(dao, DatabaseStudyDao) else ChildNotFoundError


def _assert_reset_matrix(df: pl.DataFrame) -> None:
    """Assert that a matrix was reset after a time-step change.

    Both backends are accepted: the DB DAO stores the null matrix (empty DataFrame),
    while the file DAO reads back a correctly-sized all-zero matrix from disk.
    """
    assert df.is_empty() or df.unpivot().get_column("value").unique().to_list() == [0.0]


# ──────────────────────────────────────────────────────────────────────
# Shared tests (run on both database and filesystem backends)
# ──────────────────────────────────────────────────────────────────────


def test_constraint_crud(dao: StudyDao) -> None:
    """Full CRUD lifecycle: empty → save → get → update → delete."""
    c1: ConstraintId = ConstraintId("c1")
    c2: ConstraintId = ConstraintId("c2")
    ghost: ConstraintId = ConstraintId("ghost")

    # Initially empty
    assert dao.get_all_constraints() == {}
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint(ghost)

    # Save two constraints and read them back
    bc_c1 = _bc(
        c1,
        name="C1",
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.GREATER,
        comments="my comment",
    )
    bc_c2 = _bc(
        c2,
        name="C2",
        enabled=False,
        time_step=BindingConstraintFrequency.WEEKLY,
        operator=BindingConstraintOperator.BOTH,
        comments="x",
    )
    dao.save_constraints([bc_c1, bc_c2])

    result = dao.get_all_constraints()
    assert set(result.keys()) == {c1, c2}
    r1 = dao.get_constraint(c1)
    assert r1.name == "C1" and r1.time_step == BindingConstraintFrequency.DAILY and r1.comments == "my comment"
    r2 = result[c2]
    assert r2.enabled is False and r2.operator == BindingConstraintOperator.BOTH

    # Update c2 (upsert)
    c2_updated = _bc(
        c2,
        name="C2",
        enabled=False,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.BOTH,
        comments="new comment",
    )
    dao.save_constraints([c2_updated])
    r2 = dao.get_constraint(c2)
    assert r2.time_step == BindingConstraintFrequency.HOURLY
    assert r2.operator == BindingConstraintOperator.BOTH
    assert r2.comments == "new comment"

    # save_constraints is a partial upsert: omitting c1 does NOT remove it
    assert set(dao.get_all_constraints().keys()) == {c1, c2}

    # empty list is noop
    dao.save_constraints([])
    assert set(dao.get_all_constraints().keys()) == {c1, c2}

    # Explicit delete
    dao.delete_constraints([bc_c1])
    assert c1 not in dao.get_all_constraints()
    assert c2 in dao.get_all_constraints()

    # Deleting a nonexistent constraint is a noop
    dao.delete_constraints([_bc(ghost)])


def test_constraint_terms(dao: StudyDao) -> None:
    """Terms lifecycle: save link/cluster/mixed, no terms, term replacement, cartesian-product regression."""
    lc: ConstraintId = ConstraintId("lc")
    cc: ConstraintId = ConstraintId("cc")
    mixed: ConstraintId = ConstraintId("mixed")
    empty: ConstraintId = ConstraintId("empty")
    bc_cart: ConstraintId = ConstraintId("bc_cart")

    # Link term
    dao.save_constraints([_bc(lc, terms=[ConstraintTerm(weight=3.5, data=LinkTerm(area1="area_a", area2="area_b"))])])
    r = dao.get_constraint(lc)
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, LinkTerm) and t.weight == 3.5 and t.offset is None
    assert {t.data.area1, t.data.area2} == {"area_a", "area_b"}

    # Cluster term
    dao.save_constraints(
        [_bc(cc, terms=[ConstraintTerm(weight=4.0, offset=2, data=ClusterTerm(area="area_a", cluster="cl1"))])]
    )
    r = dao.get_constraint(cc)
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, ClusterTerm) and t.data.area == "area_a" and t.data.cluster == "cl1"
    assert t.weight == 4.0 and t.offset == 2

    # Mixed terms
    dao.save_constraints(
        [
            _bc(
                mixed,
                terms=[
                    ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
                    ConstraintTerm(weight=2.0, offset=5, data=ClusterTerm(area="a", cluster="c1")),
                ],
            )
        ]
    )
    r = dao.get_constraint(mixed)
    assert len(r.terms) == 2
    assert {type(t.data) for t in r.terms} == {LinkTerm, ClusterTerm}

    # No terms
    dao.save_constraints([_bc(empty, terms=[])])
    assert dao.get_constraint(empty).terms == []

    # Cartesian product regression: 2 link + 1 cluster must yield exactly 3 terms
    dao.save_constraints(
        [
            _bc(
                bc_cart,
                terms=[
                    ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
                    ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),
                    ConstraintTerm(weight=3.0, data=ClusterTerm(area="x", cluster="y")),
                ],
            )
        ]
    )
    r = dao.get_constraint(bc_cart)
    assert len(r.terms) == 3
    assert len([t for t in r.terms if isinstance(t.data, LinkTerm)]) == 2
    assert len([t for t in r.terms if isinstance(t.data, ClusterTerm)]) == 1

    # Term replacement scenario: A B C → B C' (A removed, C updated, sibling bc2 untouched)
    bc1_v1 = _bc(
        BC1,
        terms=[
            ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
            ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),
            ConstraintTerm(weight=3.0, offset=1, data=ClusterTerm(area="x", cluster="y")),
        ],
    )
    bc2 = _bc(BC2, terms=[ConstraintTerm(weight=5.0, data=ClusterTerm(area="p", cluster="q"))])
    dao.save_constraints([bc1_v1, bc2])
    assert len(dao.get_constraint(BC1).terms) == 3

    bc1_v2 = _bc(
        BC1,
        terms=[
            # A removed
            ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),  # B unchanged
            ConstraintTerm(weight=99.0, offset=1, data=ClusterTerm(area="x", cluster="y")),  # C' updated weight
        ],
    )
    dao.save_constraints([bc1_v2, bc2])

    r = dao.get_constraint(BC1)
    assert len(r.terms) == 2
    cluster_terms = [t for t in r.terms if isinstance(t.data, ClusterTerm)]
    assert cluster_terms[0].weight == 99.0

    # bc2 must be untouched throughout
    assert dao.get_constraint(BC2).terms[0].weight == 5.0

    # Removing all terms (both link and cluster) must not leave stale rows
    dao.save_constraints([_bc(BC1, terms=[])])
    assert dao.get_constraint(BC1).terms == []

    # Removing all link terms specifically must not leave stale link rows
    dao.save_constraints([_bc(lc, terms=[ConstraintTerm(weight=1.0, data=LinkTerm(area1="x", area2="y"))])])
    assert len([t for t in dao.get_constraint(lc).terms if isinstance(t.data, LinkTerm)]) == 1
    dao.save_constraints([_bc(lc, terms=[])])
    assert dao.get_constraint(lc).terms == []


def test_version_specific_fields(dao: StudyDao) -> None:
    """filter_year_by_year, filter_synthesis and group round-trip correctly."""
    dao.save_constraints(
        [
            _bc(
                BC1,
                filter_year_by_year=[FilterOption.HOURLY, FilterOption.DAILY],
                filter_synthesis=[FilterOption.WEEKLY],
                group="my_group",
            )
        ]
    )
    r = dao.get_constraint(BC1)
    assert FilterOption.HOURLY in r.filter_year_by_year
    assert FilterOption.DAILY in r.filter_year_by_year
    assert r.filter_synthesis == [FilterOption.WEEKLY]
    assert r.group == "my_group"


def test_matrices(dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService]) -> None:
    """All four matrix types round-trip; upsert overwrites; each constraint has its own matrices."""
    dao, matrix_service = dao_and_matrix_service
    bc_a: ConstraintId = ConstraintId("bc_a")
    bc_b: ConstraintId = ConstraintId("bc_b")

    df_lt = pl.DataFrame({"lt": [0.5, 1.5]})
    df_gt = pl.DataFrame({"gt": [2.0, 3.0]})
    df_eq = pl.DataFrame({"eq": [7.0]})
    df_new = pl.DataFrame({"v": [99.0]})

    dao.save_constraints(
        [
            _bc(BC1, operator=BindingConstraintOperator.LESS),
            _bc(BC2, operator=BindingConstraintOperator.GREATER),
            _bc(BC3, operator=BindingConstraintOperator.EQUAL),
        ]
    )

    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_lt)})
    dao.save_constraint_greater_term_matrix({BC2: matrix_service.create(df_gt)})
    dao.save_constraint_equal_term_matrix({BC3: matrix_service.create(df_eq)})

    assert dao.get_constraint_less_term_matrix(BC1).equals(df_lt)
    assert dao.get_constraint_greater_term_matrix(BC2).equals(df_gt)
    assert dao.get_constraint_equal_term_matrix(BC3).equals(df_eq)

    # Upsert: saving the same matrix type twice overwrites
    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_new)})
    assert dao.get_constraint_less_term_matrix(BC1).equals(df_new)

    # Each constraint has its own independent matrices
    df_a = pl.DataFrame({"a": [1.0]})
    df_b = pl.DataFrame({"b": [2.0]})
    dao.save_constraints([_bc(bc_a), _bc(bc_b)])
    dao.save_constraint_less_term_matrix({bc_a: matrix_service.create(df_a)})
    dao.save_constraint_less_term_matrix({bc_b: matrix_service.create(df_b)})
    assert dao.get_constraint_less_term_matrix(bc_a).equals(df_a)
    assert dao.get_constraint_less_term_matrix(bc_b).equals(df_b)


def test_metadata_change_preserves_matrices(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """Changing only name, comments, or enabled must leave matrices untouched."""
    dao, matrix_service = dao_and_matrix_service
    df_lt = pl.DataFrame({"v": [42.0]})

    dao.save_constraints(
        [_bc(BC1, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY)]
    )
    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_lt)})

    # Change comments and enabled — operator and time_step stay the same
    dao.save_constraints(
        [
            _bc(
                BC1,
                comments="updated comment",
                enabled=False,
                operator=BindingConstraintOperator.LESS,
                time_step=BindingConstraintFrequency.HOURLY,
            )
        ]
    )

    r = dao.get_constraint(BC1)
    assert r.comments == "updated comment"
    assert r.enabled is False
    assert dao.get_constraint_less_term_matrix(BC1).equals(df_lt)


@pytest.mark.parametrize(
    "existing_op,new_op,initial_terms,expected,gone_terms,seed",
    [
        # single → single: rename the one matrix to the new operator's table
        (BindingConstraintOperator.LESS, BindingConstraintOperator.GREATER, ["lt"], [("gt", "lt")], ["lt"], 10.0),
        (BindingConstraintOperator.LESS, BindingConstraintOperator.EQUAL, ["lt"], [("eq", "lt")], ["lt"], 20.0),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.LESS, ["gt"], [("lt", "gt")], ["gt"], 30.0),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.EQUAL, ["gt"], [("eq", "gt")], ["gt"], 40.0),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.LESS, ["eq"], [("lt", "eq")], ["eq"], 50.0),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.GREATER, ["eq"], [("gt", "eq")], ["eq"], 60.0),
        # single → BOTH: keep existing matrix, copy it to the other BOTH slot
        (
            BindingConstraintOperator.LESS,
            BindingConstraintOperator.BOTH,
            ["lt"],
            [("lt", "lt"), ("gt", "lt")],
            [],
            70.0,
        ),
        (
            BindingConstraintOperator.GREATER,
            BindingConstraintOperator.BOTH,
            ["gt"],
            [("gt", "gt"), ("lt", "gt")],
            [],
            80.0,
        ),
        (
            BindingConstraintOperator.EQUAL,
            BindingConstraintOperator.BOTH,
            ["eq"],
            [("lt", "eq"), ("gt", "eq")],
            ["eq"],
            90.0,
        ),
        # BOTH → single: keep the relevant matrix, delete the other
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.LESS, ["lt", "gt"], [("lt", "lt")], ["gt"], 100.0),
        (
            BindingConstraintOperator.BOTH,
            BindingConstraintOperator.GREATER,
            ["lt", "gt"],
            [("gt", "gt")],
            ["lt"],
            110.0,
        ),
        (
            BindingConstraintOperator.BOTH,
            BindingConstraintOperator.EQUAL,
            ["lt", "gt"],
            [("eq", "lt")],
            ["lt", "gt"],
            120.0,
        ),
    ],
)
def test_operator_change_renames_matrix(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
    existing_op: BindingConstraintOperator,
    new_op: BindingConstraintOperator,
    initial_terms: list[str],
    expected: list[tuple[str, str]],
    gone_terms: list[str],
    seed: float,
) -> None:
    """Operator change moves matrix data to the correct typed table, mirroring update_matrices_names."""
    dao, matrix_service = dao_and_matrix_service
    error_cls = _missing_matrix_error(dao)

    term_df = {
        "lt": pl.DataFrame({"v": [seed + 1.0]}),
        "gt": pl.DataFrame({"v": [seed + 2.0]}),
        "eq": pl.DataFrame({"v": [seed + 3.0]}),
    }
    save = {
        "lt": dao.save_constraint_less_term_matrix,
        "gt": dao.save_constraint_greater_term_matrix,
        "eq": dao.save_constraint_equal_term_matrix,
    }
    get = {
        "lt": dao.get_constraint_less_term_matrix,
        "gt": dao.get_constraint_greater_term_matrix,
        "eq": dao.get_constraint_equal_term_matrix,
    }

    # Setup: save constraint with initial operator and seed matrices
    dao.save_constraints([_bc(BC1, operator=existing_op)])
    for term in initial_terms:
        save[term]({BC1: matrix_service.create(term_df[term])})

    # Act: change the operator
    dao.save_constraints([_bc(BC1, operator=new_op)])

    # Assert: operator updated, data moved to correct tables, old tables empty
    assert dao.get_constraint(BC1).operator == new_op
    for target_term, source_term in expected:
        assert get[target_term](BC1).equals(term_df[source_term])
    for term in gone_terms:
        with pytest.raises(error_cls):
            get[term](BC1)


@pytest.mark.parametrize(
    "old_ts,new_ts,operator",
    [
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.WEEKLY, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.DAILY, BindingConstraintFrequency.HOURLY, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.WEEKLY, BindingConstraintFrequency.HOURLY, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, BindingConstraintOperator.GREATER),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, BindingConstraintOperator.EQUAL),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, BindingConstraintOperator.BOTH),
    ],
)
def test_time_step_change_regenerates_matrix(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
    old_ts: BindingConstraintFrequency,
    new_ts: BindingConstraintFrequency,
    operator: BindingConstraintOperator,
) -> None:
    dao, matrix_service = dao_and_matrix_service
    df_custom = pl.DataFrame({"v": [99.0, 99.0, 99.0]})

    savers = {
        BindingConstraintOperator.LESS: [dao.save_constraint_less_term_matrix],
        BindingConstraintOperator.GREATER: [dao.save_constraint_greater_term_matrix],
        BindingConstraintOperator.EQUAL: [dao.save_constraint_equal_term_matrix],
        BindingConstraintOperator.BOTH: [
            dao.save_constraint_less_term_matrix,
            dao.save_constraint_greater_term_matrix,
        ],
    }
    getters = {
        BindingConstraintOperator.LESS: [dao.get_constraint_less_term_matrix],
        BindingConstraintOperator.GREATER: [dao.get_constraint_greater_term_matrix],
        BindingConstraintOperator.EQUAL: [dao.get_constraint_equal_term_matrix],
        BindingConstraintOperator.BOTH: [
            dao.get_constraint_less_term_matrix,
            dao.get_constraint_greater_term_matrix,
        ],
    }

    # Setup: save constraint with initial time step and non-zero matrices
    dao.save_constraints([_bc(BC1, operator=operator, time_step=old_ts)])
    for saver in savers[operator]:
        saver({BC1: matrix_service.create(df_custom)})

    # Act: change the time step
    dao.save_constraints([_bc(BC1, operator=operator, time_step=new_ts)])

    # Assert: time step updated, matrices reset to empty or all-zero default (both are accepted by the simulator)
    assert dao.get_constraint(BC1).time_step == new_ts
    for getter in getters[operator]:
        result = getter(BC1)
        _assert_reset_matrix(result)


@pytest.mark.parametrize(
    "old_ts,new_ts",
    [
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.WEEKLY),
        (BindingConstraintFrequency.DAILY, BindingConstraintFrequency.HOURLY),
        (BindingConstraintFrequency.WEEKLY, BindingConstraintFrequency.HOURLY),
    ],
)
def test_time_step_change_regenerates_matrix_pre_v87(
    dao_860_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
    old_ts: BindingConstraintFrequency,
    new_ts: BindingConstraintFrequency,
) -> None:
    dao, matrix_service = dao_860_and_matrix_service

    # Setup: save constraint with initial time step and a non-zero values matrix
    dao.save_constraints([_bc(BC1, time_step=old_ts)])
    dao.save_constraint_values_matrix({BC1: matrix_service.create(pl.DataFrame({"v": [99.0, 99.0, 99.0]}))})

    # Act: change the time step
    dao.save_constraints([_bc(BC1, time_step=new_ts)])

    # Assert: time step updated, values matrix reset to empty or all-zero default (both are accepted by the simulator)
    assert dao.get_constraint(BC1).time_step == new_ts
    result = dao.get_constraint_values_matrix(BC1)
    _assert_reset_matrix(result)


def test_time_step_and_operator_change_drops_old_matrices(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """When both time_step and operator change simultaneously, old operator's extra matrices must be deleted."""
    dao, matrix_service = dao_and_matrix_service
    error_cls = _missing_matrix_error(dao)
    df_custom = pl.DataFrame({"v": [99.0]})

    # Setup: BOTH operator (lt + gt matrices)
    dao.save_constraints(
        [_bc(BC1, operator=BindingConstraintOperator.BOTH, time_step=BindingConstraintFrequency.HOURLY)]
    )
    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_custom)})
    dao.save_constraint_greater_term_matrix({BC1: matrix_service.create(df_custom)})

    # Act: change to LESS (only lt) + new time step — gt must be deleted, lt must be zeroed
    dao.save_constraints(
        [_bc(BC1, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.DAILY)]
    )

    lt = dao.get_constraint_less_term_matrix(BC1)
    _assert_reset_matrix(lt)

    with pytest.raises(error_cls):
        dao.get_constraint_greater_term_matrix(BC1)


def test_time_step_and_operator_change_single_to_both(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """When both time_step and operator change from single→BOTH, both lt and gt must be zeroed
    to the new time step's row count. Regression: time_step_changed takes precedence over
    operator_changed in _compute_matrix_changes — this test ensures the BOTH expansion is
    handled correctly when combined with a time step reset."""
    dao, matrix_service = dao_and_matrix_service
    df_custom = pl.DataFrame({"v": [99.0]})

    # Setup: LESS + HOURLY (only lt matrix)
    dao.save_constraints(
        [_bc(BC1, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY)]
    )
    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_custom)})

    # Act: change to BOTH + DAILY — both lt and gt must be zeroed to 366 rows
    dao.save_constraints(
        [_bc(BC1, operator=BindingConstraintOperator.BOTH, time_step=BindingConstraintFrequency.DAILY)]
    )

    assert dao.get_constraint(BC1).operator == BindingConstraintOperator.BOTH
    assert dao.get_constraint(BC1).time_step == BindingConstraintFrequency.DAILY

    lt = dao.get_constraint_less_term_matrix(BC1)
    gt = dao.get_constraint_greater_term_matrix(BC1)
    _assert_reset_matrix(lt)
    _assert_reset_matrix(gt)


def test_group_update_and_scenario_builder_cleanup(dao: StudyDao) -> None:
    """Group is stored, updated, and cleared correctly; when the last constraint referencing
    a group is moved away, that group's rules are removed from the scenario builder."""
    dao.save_constraints(
        [
            _bc(BC1, group="g1"),
            _bc(BC2, group="g1"),
            _bc(BC3, group="g2"),
        ]
    )
    assert dao.get_constraint(BC1).group == "g1"
    assert dao.get_constraint(BC2).group == "g1"
    assert dao.get_constraint(BC3).group == "g2"

    dao.save_scenario_builder(Ruleset(binding_constraints={"g1": {"0": 1, "1": 2}, "g2": {"0": 3}}))

    # Move bc1 to g2 — g1 still has bc2, no scenario builder cleanup expected
    dao.save_constraints(
        [
            _bc(BC1, group="g2"),
            _bc(BC2, group="g1"),
            _bc(BC3, group="g2"),
        ]
    )
    assert dao.get_constraint(BC1).group == "g2"
    assert dao.get_constraint(BC2).group == "g1"
    assert dao.get_ruleset().binding_constraints == {"g1": {"0": 1, "1": 2}, "g2": {"0": 3}}

    # Move bc2 to g2 — g1 is now empty, must be cleaned from scenario builder
    dao.save_constraints(
        [
            _bc(BC1, group="g2"),
            _bc(BC2, group="g2"),
            _bc(BC3, group="g2"),
        ]
    )
    assert dao.get_constraint(BC2).group == "g2"
    assert dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc1's group — no scenario builder impact (g2 still has bc2 and bc3)
    dao.save_constraints(
        [
            _bc(BC1, group="default"),
        ]
    )
    assert dao.get_constraint(BC1).group == "default"
    assert dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc2's group — g2 still has bc3, no scenario builder cleanup expected
    dao.save_constraints(
        [
            _bc(BC2, group="default"),
        ]
    )
    assert dao.get_constraint(BC2).group == "default"
    assert dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc3's group — g2 is now empty, must be cleaned from scenario builder
    dao.save_constraints(
        [
            _bc(BC3, group="default"),
        ]
    )
    assert dao.get_constraint(BC3).group == "default"
    assert dao.get_ruleset().binding_constraints == {}


def test_scenario_builder_cleanup_on_constraint_removal(dao: StudyDao) -> None:
    """Deleting a constraint must trigger scenario builder cleanup
    when it was the last constraint referencing its group."""
    dao.save_constraints([_bc(BC1, group="g1"), _bc(BC2, group="g2"), _bc(BC3, group="g2")])
    dao.save_scenario_builder(Ruleset(binding_constraints={"g1": {"0": 1}, "g2": {"0": 2}}))

    # Delete bc1 — g1 has no remaining constraints, must be cleaned from scenario builder
    dao.delete_constraints([_bc(BC1, group="g1")])
    assert dao.get_ruleset().binding_constraints == {"g2": {"0": 2}}

    # Delete bc2 — g2 still has bc3, no cleanup expected
    dao.delete_constraints([_bc(BC2, group="g2")])
    assert dao.get_ruleset().binding_constraints == {"g2": {"0": 2}}

    # Delete bc3 — g2 is now empty, must be cleaned
    dao.delete_constraints([_bc(BC3, group="g2")])
    assert dao.get_ruleset().binding_constraints == {}

    # Re-create deleted constraints in the default group so the regression below can update them
    dao.save_constraints([_bc(BC1, group="default"), _bc(BC2, group="default"), _bc(BC3, group="default")])
    assert dao.get_ruleset().binding_constraints == {}

    # regression test: default group is removed when constraints are renamed to a non-default group
    dao.save_scenario_builder(Ruleset(binding_constraints={"default": {"0": 1}}))
    assert dao.get_ruleset().binding_constraints == {"default": {"0": 1}}
    dao.save_constraints([_bc(BC1, group="g1"), _bc(BC2, group="g1"), _bc(BC3, group="g1")])
    assert dao.get_ruleset().binding_constraints == {}


def test_mixed_matrix_changes_in_one_call(
    dao_and_matrix_service: tuple[StudyDao, ISimpleMatrixService],
) -> None:
    """A single save_constraints call with multiple constraints undergoing different changes
    must process each independently without cross-contamination."""
    dao, matrix_service = dao_and_matrix_service
    error_cls = _missing_matrix_error(dao)

    df_nonzero_1 = pl.DataFrame({"v": [11.0]})
    df_nonzero_2 = pl.DataFrame({"v": [22.0]})
    df_nonzero_3 = pl.DataFrame({"v": [33.0]})

    # Setup: bc1 (LESS, HOURLY), bc2 (GREATER, HOURLY), bc3 (EQUAL, HOURLY) — all with non-zero matrices
    dao.save_constraints(
        [
            _bc(BC1, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY),
            _bc(BC2, operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.HOURLY),
            _bc(BC3, operator=BindingConstraintOperator.EQUAL, time_step=BindingConstraintFrequency.HOURLY),
        ]
    )
    dao.save_constraint_less_term_matrix({BC1: matrix_service.create(df_nonzero_1)})
    dao.save_constraint_greater_term_matrix({BC2: matrix_service.create(df_nonzero_2)})
    dao.save_constraint_equal_term_matrix({BC3: matrix_service.create(df_nonzero_3)})

    # Act: bc1 changes time step, bc2 changes operator, bc3 unchanged — all in one call
    dao.save_constraints(
        [
            _bc(BC1, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.DAILY),
            _bc(BC2, operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY),
            _bc(BC3, operator=BindingConstraintOperator.EQUAL, time_step=BindingConstraintFrequency.HOURLY),
        ]
    )

    # bc1: time step reset → lt replaced with empty or all-zero default matrix
    lt1 = dao.get_constraint_less_term_matrix(BC1)
    _assert_reset_matrix(lt1)
    # bc2: operator GREATER → LESS → gt deleted, lt holds the old gt data
    lt2 = dao.get_constraint_less_term_matrix(BC2)
    assert lt2.equals(df_nonzero_2)
    with pytest.raises(error_cls):
        dao.get_constraint_greater_term_matrix(BC2)

    # bc3: unchanged → eq still holds original non-zero data
    eq3 = dao.get_constraint_equal_term_matrix(BC3)
    assert eq3.equals(df_nonzero_3)


# ──────────────────────────────────────────────────────────────────────
# Database-only tests
# ──────────────────────────────────────────────────────────────────────


def _assert_tables_empty(db_session: Session, tables: list[Table], study_id: str) -> None:
    for table in tables:
        rows = db_session.execute(select(table).where(table.c.study_id == study_id)).fetchall()
        assert rows == [], f"{table.name}: expected no rows for study {study_id}, found {len(rows)}"


def test_constraint_crud_study_isolation(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """Constraints are isolated per study."""
    c1: ConstraintId = ConstraintId("c1")
    db_dao.save_constraints([_bc(c1)])
    assert set(db_dao.get_all_constraints().keys()) == {c1}

    dao2 = build_db_dao(db_session, db_dao._matrix_service, STUDY_VERSION_8_8)
    assert dao2.get_all_constraints() == {}


def test_cascade_deletes(
    db_session: Session,
    db_dao_930_and_matrix_service: tuple[DatabaseStudyDao, ISimpleMatrixService],
) -> None:
    """Deleting a constraint or its study cascades to all child tables."""
    db_dao, matrix_service = db_dao_930_and_matrix_service
    study_id = db_dao.get_study_id()
    series_id = matrix_service.create(pl.DataFrame({"v": [1.0]}))

    constraint = _bc(
        BC1,
        terms=[
            ConstraintTerm(weight=1.0, data=LinkTerm(area1="a", area2="b")),
            ConstraintTerm(weight=2.0, data=ClusterTerm(area="a", cluster="c1")),
        ],
    )
    db_dao.save_constraints([constraint])
    db_dao.save_constraint_values_matrix({BC1: series_id})
    db_dao.save_constraint_less_term_matrix({BC1: series_id})
    db_dao.save_constraint_greater_term_matrix({BC1: series_id})
    db_dao.save_constraint_equal_term_matrix({BC1: series_id})

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
    db_dao.save_constraints([_bc(BC2, terms=[ConstraintTerm(weight=1.0, data=LinkTerm(area1="x", area2="y"))])])
    db_dao.save_constraint_less_term_matrix({BC2: series_id})

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
