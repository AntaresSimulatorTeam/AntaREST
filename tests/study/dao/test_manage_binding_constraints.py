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
#
# Mirrors tests/variantstudy/model/command/test_manage_binding_constraints.py but
# rewires the commands to use DatabaseStudyDao instead of FileStudy.
# Every command.apply() call receives a DatabaseStudyDao — the dispatch in
# ICommand.apply() then calls _apply_dao() directly.

import pytest
from sqlalchemy.orm import Session

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
)
from antarest.study.business.model.scenario_builder_model import RulesetUpdate
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7, STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.conftest import build_db_dao


def test_manage_binding_constraint(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Full binding-constraint lifecycle via commands routed through DatabaseStudyDao,
    mirroring test_manage_binding_constraint in the command-layer tests.
    """
    for study_version in [STUDY_VERSION_8_6, STUDY_VERSION_8_8]:
        db_dao = build_db_dao(db_session, matrix_service, study_version)

        area1 = "area1"
        area2 = "area2"
        cluster = "cluster"

        output = CreateBindingConstraint(
            parameters={
                "name": "BD 1",
                "time_step": BindingConstraintFrequency.HOURLY,
                "operator": BindingConstraintOperator.LESS,
                "terms": [ConstraintTerm(weight=800, offset=30, data=LinkTerm(area1=area1, area2=area2))],
                "comments": "Hello",
            },
            matrices={},
            command_context=command_context,
            study_version=study_version,
        ).apply(db_dao)
        assert output.status, output.message

        output = CreateBindingConstraint(
            parameters={
                "name": "BD 2",
                "enabled": False,
                "time_step": BindingConstraintFrequency.DAILY,
                "operator": BindingConstraintOperator.BOTH,
                "terms": [ConstraintTerm(weight=50, data=ClusterTerm(area=area1, cluster=cluster))],
            },
            matrices={},
            command_context=command_context,
            study_version=study_version,
        ).apply(db_dao)
        assert output.status, output.message

        r1 = db_dao.get_constraint("bd 1")
        assert r1.name == "BD 1"
        assert r1.time_step == BindingConstraintFrequency.HOURLY
        assert r1.operator == BindingConstraintOperator.LESS
        assert r1.comments == "Hello"
        link_term = next(t for t in r1.terms if isinstance(t.data, LinkTerm))
        assert link_term.weight == 800
        assert link_term.offset == 30

        r2 = db_dao.get_constraint("bd 2")
        assert r2.enabled is False
        assert r2.time_step == BindingConstraintFrequency.DAILY
        assert r2.operator == BindingConstraintOperator.BOTH
        cluster_term = next(t for t in r2.terms if isinstance(t.data, ClusterTerm))
        assert cluster_term.weight == 50

        if study_version < STUDY_VERSION_8_7:
            weekly_values = command_context.generator_matrix_constants.get_binding_constraint_daily_weekly_86()
            values_matrix = weekly_values
            less_term_matrix = None
            greater_term_matrix = None
        else:
            weekly_values = command_context.generator_matrix_constants.get_binding_constraint_daily_weekly_87()
            values_matrix = None
            less_term_matrix = weekly_values
            greater_term_matrix = weekly_values

        # Update BD 1: HOURLY/LESS → WEEKLY/BOTH
        output = UpdateBindingConstraint(
            id="bd 1",
            parameters={
                "enabled": False,
                "time_step": BindingConstraintFrequency.WEEKLY,
                "operator": BindingConstraintOperator.BOTH,
                "terms": [ConstraintTerm(weight=800, offset=30, data=LinkTerm(area1=area1, area2=area2))],
            },
            matrices={
                "values": values_matrix,
                "less_term_matrix": less_term_matrix,
                "greater_term_matrix": greater_term_matrix,
            },
            command_context=command_context,
            study_version=study_version,
        ).apply(db_dao)
        assert output.status, output.message

        r1 = db_dao.get_constraint("bd 1")
        assert r1.enabled is False
        assert r1.time_step == BindingConstraintFrequency.WEEKLY
        assert r1.operator == BindingConstraintOperator.BOTH
        assert r1.comments == "Hello"  # comments not changed by update

        expected_rows = 366  # both daily/weekly default matrices (v86 and v87+) have 366 rows

        if study_version < STUDY_VERSION_8_7:
            values = db_dao.get_constraint_values_matrix("bd 1")
            assert values.shape[0] == expected_rows
            assert values.to_series(0).sum() == 0.0
        else:
            lt = db_dao.get_constraint_less_term_matrix("bd 1")
            gt = db_dao.get_constraint_greater_term_matrix("bd 1")
            assert lt.shape[0] == expected_rows
            assert gt.shape[0] == expected_rows
            assert lt.to_series(0).sum() == 0.0
            assert gt.to_series(0).sum() == 0.0

        if study_version >= STUDY_VERSION_8_7:
            output = UpdateScenarioBuilder(
                data=RulesetUpdate(binding_constraints={"default": {"0": 1}}),
                command_context=command_context,
                study_version=study_version,
            ).apply(db_dao)
            assert output.status, output.message

        output = RemoveMultipleBindingConstraints(
            id="bd 1", command_context=command_context, study_version=study_version
        ).apply(db_dao)
        assert output.status, output.message

        if study_version >= STUDY_VERSION_8_7:
            # BD 2 still in "default" group → rule must survive
            assert db_dao.get_ruleset().binding_constraints == {"default": {"0": 1}}

        assert "bd 1" not in db_dao.get_all_constraints()

        with pytest.raises(BindingConstraintNotFound):
            if study_version < STUDY_VERSION_8_7:
                db_dao.get_constraint_values_matrix("bd 1")
            else:
                db_dao.get_constraint_less_term_matrix("bd 1")

        assert db_dao.get_constraint("bd 2").operator == BindingConstraintOperator.BOTH

        output = RemoveMultipleBindingConstraints(
            id="bd 2", command_context=command_context, study_version=study_version
        ).apply(db_dao)
        assert output.status, output.message

        assert db_dao.get_all_constraints() == {}

        if study_version >= STUDY_VERSION_8_7:
            assert db_dao.get_ruleset().binding_constraints == {}


def test_scenario_builder(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    Scenario builder rule is removed when a BC group is renamed, mirroring
    test_scenario_builder in the command-layer tests.
    """
    study_version = STUDY_VERSION_8_8
    db_dao = build_db_dao(db_session, matrix_service, study_version)

    output = CreateBindingConstraint(
        parameters={
            "name": "BD 1",
            "enabled": False,
            "time_step": BindingConstraintFrequency.DAILY,
            "operator": BindingConstraintOperator.BOTH,
            "group": "Group 1",
        },
        matrices={},
        command_context=command_context,
        study_version=study_version,
    ).apply(db_dao)
    assert output.status, output.message

    output = UpdateScenarioBuilder(
        data=RulesetUpdate(binding_constraints={"group 1": {"0": 1}}),
        command_context=command_context,
        study_version=study_version,
    ).apply(db_dao)
    assert output.status, output.message

    output = UpdateBindingConstraint(
        id="bd 1",
        parameters={"group": "Group 2"},
        matrices={},
        command_context=command_context,
        study_version=study_version,
    ).apply(db_dao)
    assert output.status, output.message

    # "group 1" is now orphaned → its rule is removed
    assert "group 1" not in db_dao.get_ruleset().binding_constraints


def test_update_bc_with_an_integer_name(
    db_session: Session, matrix_service: ISimpleMatrixService, command_context: CommandContext
) -> None:
    """
    A BC whose name is an integer string must survive a command round-trip, mirroring
    test_update_bc_with_an_integer_name in the command-layer tests.
    """
    study_version = STUDY_VERSION_8_8
    db_dao = build_db_dao(db_session, matrix_service, study_version)

    output = CreateBindingConstraint(
        parameters={"name": "111"},
        matrices={},
        command_context=command_context,
        study_version=study_version,
    ).apply(db_dao)
    assert output.status, output.message

    r = db_dao.get_constraint("111")
    assert r.id == "111"

    output = UpdateBindingConstraint(
        id="111",
        parameters={"comments": "Hello"},
        matrices={},
        command_context=command_context,
        study_version=study_version,
    ).apply(db_dao)
    assert output.status, output.message

    r = db_dao.get_constraint("111")
    assert r.comments == "Hello"
    assert r.id == "111"
