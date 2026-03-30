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

from antarest.core.exceptions import BindingConstraintNotFound, ChildNotFoundError
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
from antarest.study.business.model.scenario_builder_model import Ruleset
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


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


def test_constraint_crud(filestudy_dao: FileStudyTreeDao) -> None:
    """Full CRUD lifecycle: empty → save → get → update → delete."""
    # Initially empty
    assert filestudy_dao.get_all_constraints() == {}
    with pytest.raises(BindingConstraintNotFound):
        filestudy_dao.get_constraint("ghost")

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
    filestudy_dao.save_constraints([c1, c2])

    result = filestudy_dao.get_all_constraints()
    assert set(result.keys()) == {"c1", "c2"}
    r1 = filestudy_dao.get_constraint("c1")
    assert r1.name == "C1" and r1.time_step == BindingConstraintFrequency.DAILY and r1.comments == "my comment"
    r2 = result["c2"]
    assert r2.enabled is False and r2.operator == BindingConstraintOperator.BOTH

    # Update c2 (upsert)
    c2_updated = _bc(
        "c2",
        name="C2",
        enabled=False,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.BOTH,
        comments="new comment",
    )
    filestudy_dao.save_constraints([c2_updated])
    r2 = filestudy_dao.get_constraint("c2")
    assert r2.time_step == BindingConstraintFrequency.HOURLY
    assert r2.operator == BindingConstraintOperator.BOTH
    assert r2.comments == "new comment"

    # save_constraints is a partial upsert: omitting c1 does NOT remove it
    assert set(filestudy_dao.get_all_constraints().keys()) == {"c1", "c2"}

    # empty list is noop
    filestudy_dao.save_constraints([])
    assert set(filestudy_dao.get_all_constraints().keys()) == {"c1", "c2"}

    # Explicit delete
    filestudy_dao.delete_constraints([c1])
    assert "c1" not in filestudy_dao.get_all_constraints()
    assert "c2" in filestudy_dao.get_all_constraints()

    # Deleting a nonexistent constraint is a noop
    filestudy_dao.delete_constraints([_bc("ghost")])


def test_constraint_terms(filestudy_dao: FileStudyTreeDao) -> None:
    """Terms lifecycle: save link/cluster/mixed, no terms, term replacement, cartesian-product regression."""
    # Link term
    filestudy_dao.save_constraints(
        [_bc("lc", terms=[ConstraintTerm(weight=3.5, data=LinkTerm(area1="area_a", area2="area_b"))])]
    )
    r = filestudy_dao.get_constraint("lc")
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, LinkTerm) and t.weight == 3.5 and t.offset is None
    assert {t.data.area1, t.data.area2} == {"area_a", "area_b"}

    # Cluster term
    filestudy_dao.save_constraints(
        [_bc("cc", terms=[ConstraintTerm(weight=4.0, offset=2, data=ClusterTerm(area="area_a", cluster="cl1"))])]
    )
    r = filestudy_dao.get_constraint("cc")
    assert len(r.terms) == 1
    t = r.terms[0]
    assert isinstance(t.data, ClusterTerm) and t.data.area == "area_a" and t.data.cluster == "cl1"
    assert t.weight == 4.0 and t.offset == 2

    # Mixed terms
    filestudy_dao.save_constraints(
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
    r = filestudy_dao.get_constraint("mixed")
    assert len(r.terms) == 2
    assert {type(t.data) for t in r.terms} == {LinkTerm, ClusterTerm}

    # No terms
    filestudy_dao.save_constraints([_bc("empty", terms=[])])
    assert filestudy_dao.get_constraint("empty").terms == []

    # Cartesian product regression: 2 link + 1 cluster must yield exactly 3 terms
    filestudy_dao.save_constraints(
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
    r = filestudy_dao.get_constraint("bc_cart")
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
    filestudy_dao.save_constraints([bc1_v1, bc2])
    assert len(filestudy_dao.get_constraint("bc1").terms) == 3

    bc1_v2 = _bc(
        "bc1",
        terms=[
            ConstraintTerm(weight=2.0, data=LinkTerm(area1="c", area2="d")),  # B unchanged
            ConstraintTerm(weight=99.0, offset=1, data=ClusterTerm(area="x", cluster="y")),  # C' updated weight
        ],
    )
    filestudy_dao.save_constraints([bc1_v2, bc2])

    r = filestudy_dao.get_constraint("bc1")
    assert len(r.terms) == 2
    cluster_terms = [t for t in r.terms if isinstance(t.data, ClusterTerm)]
    assert cluster_terms[0].weight == 99.0

    # bc2 must be untouched throughout
    assert filestudy_dao.get_constraint("bc2").terms[0].weight == 5.0


def test_version_specific_fields(filestudy_dao: FileStudyTreeDao) -> None:
    """filter_year_by_year, filter_synthesis and group round-trip correctly; nullables stay None."""
    filestudy_dao.save_constraints(
        [
            _bc(
                "bc1",
                filter_year_by_year=[FilterOption.HOURLY, FilterOption.DAILY],
                filter_synthesis=[FilterOption.WEEKLY],
                group="my_group",
            )
        ]
    )
    r = filestudy_dao.get_constraint("bc1")
    assert FilterOption.HOURLY in r.filter_year_by_year
    assert FilterOption.DAILY in r.filter_year_by_year
    assert r.filter_synthesis == [FilterOption.WEEKLY]
    assert r.group == "my_group"

    # Unset filter fields
    filestudy_dao.save_constraints([_bc("bc2", filter_year_by_year=None, filter_synthesis=None, group=None)])
    r2 = filestudy_dao.get_constraint("bc2")
    assert r2.filter_year_by_year == []
    assert r2.filter_synthesis == []
    assert r2.group == "default"


def test_matrices(filestudy_dao_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService]) -> None:
    """All four matrix types round-trip; upsert overwrites; each constraint has its own matrices."""
    filestudy_dao, matrix_service = filestudy_dao_and_matrix_service

    df_lt = pl.DataFrame({"lt": [0.5, 1.5]})
    df_gt = pl.DataFrame({"gt": [2.0, 3.0]})
    df_eq = pl.DataFrame({"eq": [7.0]})
    df_new = pl.DataFrame({"v": [99.0]})

    filestudy_dao.save_constraints(
        [
            _bc("bc1", operator=BindingConstraintOperator.LESS),
            _bc("bc2", operator=BindingConstraintOperator.GREATER),
            _bc("bc3", operator=BindingConstraintOperator.EQUAL),
        ]
    )

    filestudy_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_lt))
    filestudy_dao.save_constraint_greater_term_matrix("bc2", matrix_service.create(df_gt))
    filestudy_dao.save_constraint_equal_term_matrix("bc3", matrix_service.create(df_eq))

    assert filestudy_dao.get_constraint_less_term_matrix("bc1").equals(df_lt)
    assert filestudy_dao.get_constraint_greater_term_matrix("bc2").equals(df_gt)
    assert filestudy_dao.get_constraint_equal_term_matrix("bc3").equals(df_eq)

    # Upsert: saving the same matrix type twice overwrites
    filestudy_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_new))
    assert filestudy_dao.get_constraint_less_term_matrix("bc1").equals(df_new)

    # Each constraint has its own independent matrices
    df_a = pl.DataFrame({"a": [1.0]})
    df_b = pl.DataFrame({"b": [2.0]})
    filestudy_dao.save_constraints([_bc("bc_a"), _bc("bc_b")])
    filestudy_dao.save_constraint_less_term_matrix("bc_a", matrix_service.create(df_a))
    filestudy_dao.save_constraint_less_term_matrix("bc_b", matrix_service.create(df_b))
    assert filestudy_dao.get_constraint_less_term_matrix("bc_a").equals(df_a)
    assert filestudy_dao.get_constraint_less_term_matrix("bc_b").equals(df_b)


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
            ["lt"],  # initially we have only lt
            [("lt", "lt"), ("gt", "lt")],  # new lt is old lt *and* new gt is old lt
            [],  # nothing removed
            70.0,
        ),
        (
            BindingConstraintOperator.GREATER,
            BindingConstraintOperator.BOTH,
            ["gt"],  # initially we have only gt
            [("gt", "gt"), ("lt", "gt")],  # new gt is old gt *and* new lt is old gt
            [],  # nothing removed
            80.0,
        ),
        (
            BindingConstraintOperator.EQUAL,
            BindingConstraintOperator.BOTH,
            ["eq"],  # initially we have only eq
            [("lt", "eq"), ("gt", "eq")],  # new gt is old eq *and* new lt is old eq
            ["eq"],  # eq is removed
            90.0,
        ),
        # BOTH → single: keep the relevant matrix, delete the other
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.LESS, ["lt", "gt"], [("lt", "lt")], ["gt"], 100.0),
        (
            BindingConstraintOperator.BOTH,
            BindingConstraintOperator.GREATER,
            ["lt", "gt"],  # initially we have lt and gt
            [("gt", "gt")],  # we only keep gt with same values
            ["lt"],  # lt is gone
            110.0,
        ),
        (
            BindingConstraintOperator.BOTH,
            BindingConstraintOperator.EQUAL,
            ["lt", "gt"],  # initially we have lt and gt
            [("eq", "lt")],  # new eq is equal to lt
            ["lt", "gt"],  # lt and gt are gone
            120.0,
        ),
    ],
)
def test_operator_change_renames_matrix(
    filestudy_dao_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService],
    existing_op: BindingConstraintOperator,
    new_op: BindingConstraintOperator,
    initial_terms: list[str],
    expected: list[tuple[str, str]],
    gone_terms: list[str],
    seed: float,
) -> None:
    """Operator change moves matrix data to the correct typed table, mirroring update_matrices_names."""
    filestudy_dao, matrix_service = filestudy_dao_and_matrix_service

    term_df = {
        "lt": pl.DataFrame({"v": [seed + 1.0]}),
        "gt": pl.DataFrame({"v": [seed + 2.0]}),
        "eq": pl.DataFrame({"v": [seed + 3.0]}),
    }
    save = {
        "lt": filestudy_dao.save_constraint_less_term_matrix,
        "gt": filestudy_dao.save_constraint_greater_term_matrix,
        "eq": filestudy_dao.save_constraint_equal_term_matrix,
    }
    get = {
        "lt": filestudy_dao.get_constraint_less_term_matrix,
        "gt": filestudy_dao.get_constraint_greater_term_matrix,
        "eq": filestudy_dao.get_constraint_equal_term_matrix,
    }

    # Setup: save constraint with initial operator and seed matrices
    filestudy_dao.save_constraints([_bc("bc1", operator=existing_op)])
    for term in initial_terms:
        save[term]("bc1", matrix_service.create(term_df[term]))

    # Act: change the operator
    filestudy_dao.save_constraints([_bc("bc1", operator=new_op)])

    # Assert: operator updated, data moved to correct tables, old tables empty
    assert filestudy_dao.get_constraint("bc1").operator == new_op
    for target_term, source_term in expected:
        assert get[target_term]("bc1").equals(term_df[source_term])
    for term in gone_terms:
        with pytest.raises(ChildNotFoundError):
            get[term]("bc1")


@pytest.mark.parametrize(
    "old_ts,new_ts,expected_rows,operator",
    [
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, 366, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.WEEKLY, 366, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.DAILY, BindingConstraintFrequency.HOURLY, 8784, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.WEEKLY, BindingConstraintFrequency.HOURLY, 8784, BindingConstraintOperator.LESS),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, 366, BindingConstraintOperator.GREATER),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, 366, BindingConstraintOperator.EQUAL),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, 366, BindingConstraintOperator.BOTH),
    ],
)
def test_time_step_change_regenerates_matrix(
    filestudy_dao_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService],
    old_ts: BindingConstraintFrequency,
    new_ts: BindingConstraintFrequency,
    expected_rows: int,
    operator: BindingConstraintOperator,
) -> None:
    filestudy_dao, matrix_service = filestudy_dao_and_matrix_service
    df_custom = pl.DataFrame({"v": [99.0, 99.0, 99.0]})

    savers = {
        BindingConstraintOperator.LESS: [filestudy_dao.save_constraint_less_term_matrix],
        BindingConstraintOperator.GREATER: [filestudy_dao.save_constraint_greater_term_matrix],
        BindingConstraintOperator.EQUAL: [filestudy_dao.save_constraint_equal_term_matrix],
        BindingConstraintOperator.BOTH: [
            filestudy_dao.save_constraint_less_term_matrix,
            filestudy_dao.save_constraint_greater_term_matrix,
        ],
    }
    getters = {
        BindingConstraintOperator.LESS: [filestudy_dao.get_constraint_less_term_matrix],
        BindingConstraintOperator.GREATER: [filestudy_dao.get_constraint_greater_term_matrix],
        BindingConstraintOperator.EQUAL: [filestudy_dao.get_constraint_equal_term_matrix],
        BindingConstraintOperator.BOTH: [
            filestudy_dao.get_constraint_less_term_matrix,
            filestudy_dao.get_constraint_greater_term_matrix,
        ],
    }

    # Setup: save constraint with initial time step and non-zero matrices
    filestudy_dao.save_constraints([_bc("bc1", operator=operator, time_step=old_ts)])
    for saver in savers[operator]:
        saver("bc1", matrix_service.create(df_custom))

    # Act: change the time step
    filestudy_dao.save_constraints([_bc("bc1", operator=operator, time_step=new_ts)])

    # Assert: time step updated, matrices replaced with all-zero defaults of the new shape
    assert filestudy_dao.get_constraint("bc1").time_step == new_ts
    for getter in getters[operator]:
        result = getter("bc1")
        assert result.shape == (expected_rows, 1)  # 8.7+ one column
        assert result.to_series(0).sum() == 0.0


@pytest.mark.parametrize(
    "old_ts,new_ts,expected_rows",
    [
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.DAILY, 366),
        (BindingConstraintFrequency.HOURLY, BindingConstraintFrequency.WEEKLY, 366),
        (BindingConstraintFrequency.DAILY, BindingConstraintFrequency.HOURLY, 8784),
        (BindingConstraintFrequency.WEEKLY, BindingConstraintFrequency.HOURLY, 8784),
    ],
)
def test_time_step_change_regenerates_matrix_pre_v87(
    filestudy_dao_860_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService],
    old_ts: BindingConstraintFrequency,
    new_ts: BindingConstraintFrequency,
    expected_rows: int,
) -> None:
    filestudy_dao, matrix_service = filestudy_dao_860_and_matrix_service

    # Setup: save constraint with initial time step and a non-zero values matrix
    filestudy_dao.save_constraints([_bc("bc1", time_step=old_ts)])
    filestudy_dao.save_constraint_values_matrix("bc1", matrix_service.create(pl.DataFrame({"v": [99.0, 99.0, 99.0]})))

    # Act: change the time step
    filestudy_dao.save_constraints([_bc("bc1", time_step=new_ts)])

    # Assert: time step updated, values matrix replaced with all-zero default of the new shape
    assert filestudy_dao.get_constraint("bc1").time_step == new_ts
    result = filestudy_dao.get_constraint_values_matrix("bc1")
    assert result.shape == (expected_rows, 3)  # 8.6- three columns
    assert result.to_series(0).sum() == 0.0


def test_time_step_and_operator_change_drops_old_matrices(
    filestudy_dao_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService],
) -> None:
    """When both time_step and operator change simultaneously, old operator's extra matrices must be deleted.

    Regression target: the `for term in OPERATOR_MATRICES_MAP[old.operator]: to_delete[term]...`
    in the time_step_changed branch. Without that delete, switching from BOTH (lt+gt) to LESS (lt only)
    leaves the gt matrix in the DB even after the time step reset.
    """
    filestudy_dao, matrix_service = filestudy_dao_and_matrix_service
    df_custom = pl.DataFrame({"v": [99.0]})

    # Setup: BOTH operator (lt + gt matrices)
    filestudy_dao.save_constraints(
        [_bc("bc1", operator=BindingConstraintOperator.BOTH, time_step=BindingConstraintFrequency.HOURLY)]
    )
    filestudy_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_custom))
    filestudy_dao.save_constraint_greater_term_matrix("bc1", matrix_service.create(df_custom))

    # Act: change to LESS (only lt) + new time step — gt must be deleted, lt must be zeroed
    filestudy_dao.save_constraints(
        [_bc("bc1", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.DAILY)]
    )

    result = filestudy_dao.get_constraint_less_term_matrix("bc1")
    assert result.shape == (366, 1)
    assert result.to_series(0).sum() == 0.0

    with pytest.raises(ChildNotFoundError):
        filestudy_dao.get_constraint_greater_term_matrix("bc1")


def test_group_update_and_scenario_builder_cleanup(filestudy_dao: FileStudyTreeDao) -> None:
    """Group is stored, updated, and cleared correctly; when the last constraint referencing
    a group is moved away, that group's rules are removed from the scenario builder."""
    filestudy_dao.save_constraints(
        [
            _bc("bc1", group="g1"),
            _bc("bc2", group="g1"),
            _bc("bc3", group="g2"),
        ]
    )
    assert filestudy_dao.get_constraint("bc1").group == "g1"
    assert filestudy_dao.get_constraint("bc2").group == "g1"
    assert filestudy_dao.get_constraint("bc3").group == "g2"

    filestudy_dao.save_scenario_builder(Ruleset(binding_constraints={"g1": {"0": 1, "1": 2}, "g2": {"0": 3}}))

    # Move bc1 to g2 — g1 still has bc2, no scenario builder cleanup expected
    filestudy_dao.save_constraints(
        [
            _bc("bc1", group="g2"),
            _bc("bc2", group="g1"),
            _bc("bc3", group="g2"),
        ]
    )
    assert filestudy_dao.get_constraint("bc1").group == "g2"
    assert filestudy_dao.get_constraint("bc2").group == "g1"
    assert filestudy_dao.get_ruleset().binding_constraints == {"g1": {"0": 1, "1": 2}, "g2": {"0": 3}}

    # Move bc2 to g2 — g1 is now empty, must be cleaned from scenario builder
    filestudy_dao.save_constraints(
        [
            _bc("bc1", group="g2"),
            _bc("bc2", group="g2"),
            _bc("bc3", group="g2"),
        ]
    )
    assert filestudy_dao.get_constraint("bc2").group == "g2"
    assert filestudy_dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc1's group — no scenario builder impact (g2 still has bc2 and bc3)
    filestudy_dao.save_constraints(
        [
            _bc("bc1", group=None),
        ]
    )
    assert filestudy_dao.get_constraint("bc1").group == "default"
    assert filestudy_dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc2's group — g2 still has bc3, no scenario builder cleanup expected
    filestudy_dao.save_constraints(
        [
            _bc("bc2", group=None),
        ]
    )
    assert filestudy_dao.get_constraint("bc2").group == "default"
    assert filestudy_dao.get_ruleset().binding_constraints == {"g2": {"0": 3}}

    # Clear bc3's group — g2 is now empty, must be cleaned from scenario builder
    filestudy_dao.save_constraints(
        [
            _bc("bc3", group=None),
        ]
    )
    assert filestudy_dao.get_constraint("bc3").group == "default"
    assert filestudy_dao.get_ruleset().binding_constraints == {}


def test_scenario_builder_cleanup_on_constraint_removal(filestudy_dao: FileStudyTreeDao) -> None:
    """Deleting a constraint must trigger scenario builder cleanup
    when it was the last constraint referencing its group."""
    filestudy_dao.save_constraints([_bc("bc1", group="g1"), _bc("bc2", group="g2"), _bc("bc3", group="g2")])
    filestudy_dao.save_scenario_builder(Ruleset(binding_constraints={"g1": {"0": 1}, "g2": {"0": 2}}))

    # Delete bc1 — g1 has no remaining constraints, must be cleaned from scenario builder
    filestudy_dao.delete_constraints([_bc("bc1", group="g1")])
    assert filestudy_dao.get_ruleset().binding_constraints == {"g2": {"0": 2}}

    # Delete bc2 — g2 still has bc3, no cleanup expected
    filestudy_dao.delete_constraints([_bc("bc2", group="g2")])
    assert filestudy_dao.get_ruleset().binding_constraints == {"g2": {"0": 2}}

    # Delete bc3 — g2 is now empty, must be cleaned
    filestudy_dao.delete_constraints([_bc("bc3", group="g2")])
    assert filestudy_dao.get_ruleset().binding_constraints == {}


def test_mixed_matrix_changes_in_one_call(
    filestudy_dao_and_matrix_service: tuple[FileStudyTreeDao, ISimpleMatrixService],
) -> None:
    """A single save_constraints call with multiple constraints undergoing different changes
    must process each independently without cross-contamination."""
    filestudy_dao, matrix_service = filestudy_dao_and_matrix_service

    df_nonzero_1 = pl.DataFrame({"v": [11.0]})
    df_nonzero_2 = pl.DataFrame({"v": [22.0]})
    df_nonzero_3 = pl.DataFrame({"v": [33.0]})

    # Setup: bc1 (LESS, HOURLY), bc2 (GREATER, HOURLY), bc3 (EQUAL, HOURLY) — all with non-zero matrices
    filestudy_dao.save_constraints(
        [
            _bc("bc1", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY),
            _bc("bc2", operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.HOURLY),
            _bc("bc3", operator=BindingConstraintOperator.EQUAL, time_step=BindingConstraintFrequency.HOURLY),
        ]
    )
    filestudy_dao.save_constraint_less_term_matrix("bc1", matrix_service.create(df_nonzero_1))
    filestudy_dao.save_constraint_greater_term_matrix("bc2", matrix_service.create(df_nonzero_2))
    filestudy_dao.save_constraint_equal_term_matrix("bc3", matrix_service.create(df_nonzero_3))

    # Act: bc1 changes time step, bc2 changes operator, bc3 unchanged — all in one call
    filestudy_dao.save_constraints(
        [
            _bc("bc1", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.DAILY),
            _bc("bc2", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY),
            _bc("bc3", operator=BindingConstraintOperator.EQUAL, time_step=BindingConstraintFrequency.HOURLY),
        ]
    )

    # bc1: time step reset → lt zeroed to 366 rows
    lt1 = filestudy_dao.get_constraint_less_term_matrix("bc1")
    assert lt1.shape == (366, 1) and lt1.to_series(0).sum() == 0.0

    # bc2: operator GREATER → LESS → gt deleted, lt holds the old gt data
    lt2 = filestudy_dao.get_constraint_less_term_matrix("bc2")
    assert lt2.equals(df_nonzero_2)
    with pytest.raises(ChildNotFoundError):
        filestudy_dao.get_constraint_greater_term_matrix("bc2")

    # bc3: unchanged → eq still holds original non-zero data
    eq3 = filestudy_dao.get_constraint_equal_term_matrix("bc3")
    assert eq3.equals(df_nonzero_3)
