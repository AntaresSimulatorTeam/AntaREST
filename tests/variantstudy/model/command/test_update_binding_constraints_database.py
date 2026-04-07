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
from sqlalchemy.orm import Session

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.matrixstore.service import ISimpleMatrixService
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
from tests.study.dao.conftest import build_db_dao

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


def test_apply_database(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Pre-seed bc_1 (GREATER/DAILY/old_group1) and bc_2 (LESS/HOURLY/old_group2),
    then run UpdateBindingConstraints with new group, operator and time_step,
    and assert the persisted state via dao.get_constraint().
    """
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_7)

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

    output = cmd.apply(dao)
    assert output.status is True

    # bc_1: group must be updated to new_group1, other fields unchanged
    bc1 = dao.get_constraint("bc_1")
    assert bc1.group == "new_group1"
    assert bc1.operator == BindingConstraintOperator.GREATER
    assert bc1.time_step == BindingConstraintFrequency.DAILY

    # bc_2: group must be updated to new_group2, other fields unchanged
    bc2 = dao.get_constraint("bc_2")
    assert bc2.group == "new_group2"
    assert bc2.operator == BindingConstraintOperator.LESS
    assert bc2.time_step == BindingConstraintFrequency.HOURLY

    # bc_0 and bc_3 must be completely untouched
    bc0 = dao.get_constraint("bc_0")
    assert bc0.group == "old_group1"

    bc3 = dao.get_constraint("bc_3")
    assert bc3.group == "old_group2"


# ---------------------------------------------------------------------------
# test_update_time_step_via_table_mode — DB equivalent of the FS-backed test
# ---------------------------------------------------------------------------


def test_update_time_step_via_table_mode_database(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Mirror of test_update_time_step_via_table_mode:
    - Create bc1 with HOURLY / LESS via CreateBindingConstraint.
    - Assert initial state.
    - Update time_step to DAILY via UpdateBindingConstraints.
    - Assert persisted time_step is DAILY; operator must still be LESS.
    """
    study_version = STUDY_VERSION_8_8
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, study_version)

    # Create the constraint through the command so that the full command pipeline is exercised
    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc1",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": study_version,
        },
        context=CommandValidationContext(version=1),
    )

    output = create_cmd.apply(dao)
    assert output.status is True

    # Verify initial state
    bc1 = dao.get_constraint("bc1")
    assert bc1.time_step == BindingConstraintFrequency.HOURLY
    assert bc1.operator == BindingConstraintOperator.LESS

    # Update only the time_step (operator must be preserved)
    update_cmd = UpdateBindingConstraints(
        study_version=study_version,
        bc_props_by_id={"bc1": BindingConstraintUpdate(time_step=BindingConstraintFrequency.DAILY)},
        command_context=command_context,
    )

    output = update_cmd.apply(dao)
    assert output.status is True

    # Assert the persisted state
    bc1_updated = dao.get_constraint("bc1")
    assert bc1_updated.time_step == BindingConstraintFrequency.DAILY
    assert bc1_updated.operator == BindingConstraintOperator.LESS  # unchanged


# ---------------------------------------------------------------------------
# test_apply_unknown_bc — updating a non-existent constraint must fail
# ---------------------------------------------------------------------------


def test_apply_unknown_bc_database(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    UpdateBindingConstraints must return a failed output when the requested bc_id
    is not present in the DAO (no pre-existing row).
    """
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_7)

    cmd = UpdateBindingConstraints(
        study_version=STUDY_VERSION_8_7,
        bc_props_by_id={"does_not_exist": BindingConstraintUpdate(group="g")},
        command_context=command_context,
    )

    output = cmd.apply(dao)
    assert output.status is False


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


def test_time_step_change_resets_matrices(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Changing time_step (HOURLY → DAILY) must reset the lt matrix to the zero matrix
    for the new time step (366 rows × 1 col, all zeros).

    Equivalent to: generate_replacement_matrices(bc_id, v8.7, DAILY, LESS) → 1 path reset.
    The DB implementation stores the actual zero-matrix ID in the lt table row
    instead of writing empty file content.
    """
    study_version = STUDY_VERSION_9_3
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, study_version)

    # --- Create bc1: LESS / HOURLY ---
    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc1",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": study_version,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    # Initial lt matrix must exist and be HOURLY-shaped (8784 rows × 1 col)
    lt_initial = dao.get_constraint_less_term_matrix("bc1")
    assert lt_initial.shape == (8784, 1)
    assert lt_initial.sum().sum_horizontal().item() == 0  # all-zero default

    # gt and eq were never created for a LESS constraint
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc1")
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc1")

    # --- Update time_step: HOURLY → DAILY ---
    update_cmd = UpdateBindingConstraints(
        study_version=study_version,
        bc_props_by_id={"bc1": BindingConstraintUpdate(time_step=BindingConstraintFrequency.DAILY)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    # Persisted metadata
    bc1 = dao.get_constraint("bc1")
    assert bc1.time_step == BindingConstraintFrequency.DAILY
    assert bc1.operator == BindingConstraintOperator.LESS  # unchanged

    # lt matrix must now be reset to the DAILY-shaped zero matrix (366 rows × 1 col)
    lt_after = dao.get_constraint_less_term_matrix("bc1")
    assert lt_after.shape == (366, 1)
    assert lt_after.sum().sum_horizontal().item() == 0

    # gt and eq still do not exist
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc1")
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc1")


def test_operator_change_moves_matrices(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Changing operator (LESS → GREATER) must:
      - copy the existing lt matrix ID to the gt table
      - delete the lt table row

    Equivalent to: generate_replacement_matrices(bc_id, v8.7, HOURLY, GREATER) → 1 path,
    but in the DB backend the old data is preserved (aliased) rather than reset.
    """
    study_version = STUDY_VERSION_9_3
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, study_version)

    # --- Create bc2: LESS / HOURLY ---
    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc2",
            "time_step": BindingConstraintFrequency.HOURLY,
            "operator": BindingConstraintOperator.LESS,
            "command_context": command_context,
            "study_version": study_version,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    lt_initial = dao.get_constraint_less_term_matrix("bc2")
    assert lt_initial.shape == (8784, 1)

    # --- Update operator: LESS → GREATER ---
    update_cmd = UpdateBindingConstraints(
        study_version=study_version,
        bc_props_by_id={"bc2": BindingConstraintUpdate(operator=BindingConstraintOperator.GREATER)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    # Persisted metadata
    bc2 = dao.get_constraint("bc2")
    assert bc2.operator == BindingConstraintOperator.GREATER
    assert bc2.time_step == BindingConstraintFrequency.HOURLY  # unchanged

    # gt must now carry the original lt data (aliased matrix ID, same shape)
    gt_after = dao.get_constraint_greater_term_matrix("bc2")
    assert gt_after.shape == (8784, 1)
    assert gt_after.equals(lt_initial)

    # lt row must have been removed
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_less_term_matrix("bc2")

    # eq was never touched
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_equal_term_matrix("bc2")


def test_operator_change_both_to_less(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Changing operator from BOTH → LESS must:
      - keep the lt row (lt is in both BOTH and LESS)
      - delete the gt row

    This mirrors the BOTH/DAILY case in test_generate_replacement_matrices.
    """
    study_version = STUDY_VERSION_9_3
    dao: DatabaseStudyDao = build_db_dao(db_session, matrix_service, study_version)

    # Create bc3: BOTH / DAILY
    create_cmd = CreateBindingConstraint.model_validate(
        {
            "name": "bc3",
            "time_step": BindingConstraintFrequency.DAILY,
            "operator": BindingConstraintOperator.BOTH,
            "command_context": command_context,
            "study_version": study_version,
        },
        context=CommandValidationContext(version=1),
    )
    assert create_cmd.apply(dao).status is True

    lt_initial = dao.get_constraint_less_term_matrix("bc3")
    gt_initial = dao.get_constraint_greater_term_matrix("bc3")
    assert lt_initial.shape == (366, 1)
    assert gt_initial.shape == (366, 1)

    # Update operator: BOTH → LESS
    update_cmd = UpdateBindingConstraints(
        study_version=study_version,
        bc_props_by_id={"bc3": BindingConstraintUpdate(operator=BindingConstraintOperator.LESS)},
        command_context=command_context,
    )
    assert update_cmd.apply(dao).status is True

    bc3 = dao.get_constraint("bc3")
    assert bc3.operator == BindingConstraintOperator.LESS

    # lt must still be present and unchanged
    lt_after = dao.get_constraint_less_term_matrix("bc3")
    assert lt_after.equals(lt_initial)

    # gt must have been removed
    with pytest.raises(BindingConstraintNotFound):
        dao.get_constraint_greater_term_matrix("bc3")
