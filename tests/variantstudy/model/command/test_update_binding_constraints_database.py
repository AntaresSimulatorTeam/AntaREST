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
Database-backed equivalent of test_update_binding_constraints.py.

These tests exercise UpdateBindingConstraints (and CreateBindingConstraint) against
a real DatabaseStudyDao, asserting results via dao.get_constraint() / dao.get_all_constraints()
instead of mock tree-save calls or filesystem reads.
"""

import pytest

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintUpdate,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_8_7, STUDY_VERSION_8_8, STUDY_VERSION_9_3
from antarest.study.storage.variantstudy.command_factory import CommandValidationContext
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_binding_constraints import UpdateBindingConstraints
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bc(name: str, **kwargs: object) -> BindingConstraint:
    """Minimal BindingConstraint factory for use in tests."""
    defaults: dict = {
        "name": name,
        "group": "default",
        "operator": BindingConstraintOperator.EQUAL,
        "time_step": BindingConstraintFrequency.HOURLY,
        "terms": [],
    }
    defaults.update(kwargs)
    return BindingConstraint(**defaults)


# ---------------------------------------------------------------------------
# test_apply — DB equivalent of the mock-based test_apply
# ---------------------------------------------------------------------------


def test_apply_database(db_dao_87: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Pre-seed bc_1 (GREATER/DAILY/old_group1) and bc_2 (LESS/HOURLY/old_group2),
    then run UpdateBindingConstraints with new group, operator and time_step,
    and assert the persisted state via dao.get_constraint().
    """
    dao = db_dao_87

    # Seed initial constraints (bc_0 acts as an unrelated constraint that must stay untouched)
    dao.save_constraints(
        [
            _bc(
                "bc_0",
                group="old_group1",
                operator=BindingConstraintOperator.GREATER,
                time_step=BindingConstraintFrequency.DAILY,
            ),
            _bc(
                "bc_1",
                group="old_group1",
                operator=BindingConstraintOperator.GREATER,
                time_step=BindingConstraintFrequency.DAILY,
            ),
            _bc(
                "bc_2",
                group="old_group2",
                operator=BindingConstraintOperator.LESS,
                time_step=BindingConstraintFrequency.HOURLY,
            ),
            _bc(
                "bc_3",
                group="old_group2",
                operator=BindingConstraintOperator.LESS,
                time_step=BindingConstraintFrequency.HOURLY,
            ),
        ]
    )

    cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_8_7,
        bc_props_by_id={
            "bc_1": BindingConstraintUpdate(
                group="new_group1",
                operator=BindingConstraintOperator.GREATER,
                time_step=BindingConstraintFrequency.DAILY,
            ),
            "bc_2": BindingConstraintUpdate(
                group="new_group2", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY
            ),
        },
        command_context=command_context,
    )

    assert cmd.apply(dao).status is True

    bc1 = dao.get_constraint("bc_1")
    assert bc1.group == "new_group1"
    assert bc1.operator == BindingConstraintOperator.GREATER
    assert bc1.time_step == BindingConstraintFrequency.DAILY

    bc2 = dao.get_constraint("bc_2")
    assert bc2.group == "new_group2"
    assert bc2.operator == BindingConstraintOperator.LESS
    assert bc2.time_step == BindingConstraintFrequency.HOURLY

    # bc_0 and bc_3 must be completely untouched
    assert dao.get_constraint("bc_0").group == "old_group1"
    assert dao.get_constraint("bc_3").group == "old_group2"


# ---------------------------------------------------------------------------
# test_update_time_step_via_table_mode — DB equivalent of the FS-backed test
# ---------------------------------------------------------------------------


def test_update_time_step_via_table_mode_database(db_dao_88: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Mirror of test_update_time_step_via_table_mode:
    - Create bc1 with HOURLY / LESS via CreateBindingConstraint.
    - Assert initial state.
    - Update time_step to DAILY via UpdateBindingConstraints.
    - Assert persisted time_step is DAILY; operator must still be LESS.
    """
    dao = db_dao_88

    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc1",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": STUDY_VERSION_8_8,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    bc1 = dao.get_constraint("bc1")
    assert bc1.time_step == BindingConstraintFrequency.HOURLY
    assert bc1.operator == BindingConstraintOperator.LESS

    update_cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_8_8,
        bc_props_by_id={"bc1": BindingConstraintUpdate(time_step=BindingConstraintFrequency.DAILY)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    bc1_updated = dao.get_constraint("bc1")
    assert bc1_updated.time_step == BindingConstraintFrequency.DAILY
    assert bc1_updated.operator == BindingConstraintOperator.LESS  # unchanged


# ---------------------------------------------------------------------------
# test_apply_unknown_bc — updating a non-existent constraint must fail
# ---------------------------------------------------------------------------


def test_apply_unknown_bc_database(db_dao_87: DatabaseStudyDao, command_context: CommandContext) -> None:
    """UpdateBindingConstraints must return a failed output when the requested bc_id is not present."""
    cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_8_7,
        bc_props_by_id={"does_not_exist": BindingConstraintUpdate(group="g")},
        command_context=command_context,
    )
    assert cmd.apply(db_dao_87).status is False


# ---------------------------------------------------------------------------
# test_to_dto — pure serialisation test, identical to the FS version
# ---------------------------------------------------------------------------


def test_to_dto(command_context: CommandContext) -> None:
    cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_8_7,
        bc_props_by_id={
            "bc_1": BindingConstraintUpdate(
                group="new_group1",
                operator=BindingConstraintOperator.GREATER,
                time_step=BindingConstraintFrequency.DAILY,
            ),
            "bc_2": BindingConstraintUpdate(
                group="new_group2", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.HOURLY
            ),
        },
        command_context=command_context,
    )
    dto = cmd.to_dto()
    assert dto.action == "update_binding_constraints"
    assert dto.version == 2
    assert dto.study_version == STUDY_VERSION_8_7


# ---------------------------------------------------------------------------
# Matrix tests — DB equivalents of test_generate_replacement_matrices
# ---------------------------------------------------------------------------


def test_time_step_change_resets_matrices(db_dao_93: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Changing time_step (HOURLY → DAILY) must reset the lt matrix to an empty or all-zero matrix.
    The null matrix is stored; the simulator fills in correctly-sized zeros at runtime.
    """
    dao = db_dao_93

    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc1",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": STUDY_VERSION_9_3,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    lt_initial = dao.get_constraint_less_term_matrix("bc1")
    assert lt_initial.shape == (8784, 1)
    assert lt_initial.sum().sum_horizontal().item() == 0

    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc1")
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc1")

    update_cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_9_3,
        bc_props_by_id={"bc1": BindingConstraintUpdate(time_step=BindingConstraintFrequency.DAILY)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    bc1 = dao.get_constraint("bc1")
    assert bc1.time_step == BindingConstraintFrequency.DAILY
    assert bc1.operator == BindingConstraintOperator.LESS  # unchanged

    lt_after = dao.get_constraint_less_term_matrix("bc1")
    assert lt_after.is_empty() or lt_after.sum().sum_horizontal().item() == 0

    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc1")
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc1")


def test_operator_change_moves_matrices(db_dao_93: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Changing operator (LESS → GREATER) must copy the lt matrix ID to gt and delete lt.
    The old data is preserved (aliased) rather than reset.
    """
    dao = db_dao_93

    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc2",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": STUDY_VERSION_9_3,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    lt_initial = dao.get_constraint_less_term_matrix("bc2")
    assert lt_initial.shape == (8784, 1)

    update_cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_9_3,
        bc_props_by_id={"bc2": BindingConstraintUpdate(operator=BindingConstraintOperator.GREATER)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    bc2 = dao.get_constraint("bc2")
    assert bc2.operator == BindingConstraintOperator.GREATER
    assert bc2.time_step == BindingConstraintFrequency.HOURLY  # unchanged

    gt_after = dao.get_constraint_greater_term_matrix("bc2")
    assert gt_after.shape == (8784, 1)
    assert gt_after.equals(lt_initial)

    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_less_term_matrix("bc2")
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc2")


def test_operator_change_both_to_less(db_dao_93: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Changing operator from BOTH → LESS must keep lt and delete gt.
    """
    dao = db_dao_93

    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc3",
            "time_step": BindingConstraintFrequency.DAILY,
            "operator": BindingConstraintOperator.BOTH,
            "command_context": command_context,
            "study_version": STUDY_VERSION_9_3,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    lt_initial = dao.get_constraint_less_term_matrix("bc3")
    gt_initial = dao.get_constraint_greater_term_matrix("bc3")
    assert lt_initial.shape == (366, 1)
    assert gt_initial.shape == (366, 1)

    update_cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_9_3,
        bc_props_by_id={"bc3": BindingConstraintUpdate(operator=BindingConstraintOperator.LESS)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    assert dao.get_constraint("bc3").operator == BindingConstraintOperator.LESS
    assert dao.get_constraint_less_term_matrix("bc3").equals(lt_initial)

    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc3")
