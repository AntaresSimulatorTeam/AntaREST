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
# Mirrors test_manage_binding_constraints.py but rewires the commands to use
# DatabaseStudyDao instead of FileStudy.
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
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7, STUDY_VERSION_8_8
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.conftest import build_db_dao


@pytest.fixture
def db_dao(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)


@pytest.fixture
def db_dao_860(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDao:
    return build_db_dao(db_session, matrix_service, STUDY_VERSION_8_6)


def test_manage_binding_constraint(
    db_dao_860: DatabaseStudyDao,
    db_dao: DatabaseStudyDao,
    command_context: CommandContext,
) -> None:
    for db_dao_versioned in [db_dao_860, db_dao]:
        study_version = db_dao_versioned.get_version()

        output = CreateBindingConstraint(
            **{
                "parameters": {
                    "name": "BD 1",
                    "time_step": BindingConstraintFrequency.HOURLY,
                    "operator": BindingConstraintOperator.LESS,
                    "terms": [ConstraintTerm(weight=800, offset=30, data=LinkTerm(area1="area1", area2="area2"))],
                    "comments": "Hello",
                },
                "matrices": {},
                "command_context": command_context,
                "study_version": study_version,
            }
        ).apply(db_dao_versioned)
        assert output.status, output.message

        output = CreateBindingConstraint(
            **{
                "parameters": {
                    "name": "BD 2",
                    "enabled": False,
                    "time_step": BindingConstraintFrequency.DAILY,
                    "operator": BindingConstraintOperator.BOTH,
                    "terms": [ConstraintTerm(weight=50, data=ClusterTerm(area="area1", cluster="cluster"))],
                },
                "matrices": {},
                "command_context": command_context,
                "study_version": study_version,
            }
        ).apply(db_dao_versioned)
        assert output.status, output.message

        bd1 = db_dao_versioned.get_constraint("bd 1")
        assert bd1.name == "BD 1"
        assert bd1.enabled is True
        assert bd1.comments == "Hello"
        assert bd1.time_step == BindingConstraintFrequency.HOURLY
        assert bd1.operator == BindingConstraintOperator.LESS
        assert len(bd1.terms) == 1
        assert isinstance(bd1.terms[0].data, LinkTerm)
        assert bd1.terms[0].weight == 800
        assert bd1.terms[0].offset == 30

        if study_version >= STUDY_VERSION_8_7:
            # LESS → only lt table populated
            db_dao_versioned.get_constraint_less_term_matrix("bd 1")
            with pytest.raises(BindingConstraintNotFound):
                db_dao_versioned.get_constraint_greater_term_matrix("bd 1")
            with pytest.raises(BindingConstraintNotFound):
                db_dao_versioned.get_constraint_equal_term_matrix("bd 1")
            # BOTH → lt and gt tables populated
            db_dao_versioned.get_constraint_less_term_matrix("bd 2")
            db_dao_versioned.get_constraint_greater_term_matrix("bd 2")
            with pytest.raises(BindingConstraintNotFound):
                db_dao_versioned.get_constraint_equal_term_matrix("bd 2")
        else:
            # Pre-8.7: single values table regardless of operator
            db_dao_versioned.get_constraint_values_matrix("bd 1")
            db_dao_versioned.get_constraint_values_matrix("bd 2")

        bd2 = db_dao_versioned.get_constraint("bd 2")
        assert bd2.name == "BD 2"
        assert bd2.enabled is False
        assert bd2.time_step == BindingConstraintFrequency.DAILY
        assert bd2.operator == BindingConstraintOperator.BOTH
        assert len(bd2.terms) == 1
        assert isinstance(bd2.terms[0].data, ClusterTerm)
        assert bd2.terms[0].weight == 50

        output = UpdateBindingConstraint(
            **{
                "id": "bd 1",
                "parameters": {
                    "enabled": False,
                    "time_step": BindingConstraintFrequency.WEEKLY,
                    "operator": BindingConstraintOperator.BOTH,
                    "terms": [ConstraintTerm(weight=800, offset=30, data=LinkTerm(area1="area1", area2="area2"))],
                },
                "matrices": {},
                "command_context": command_context,
                "study_version": study_version,
            }
        ).apply(db_dao_versioned)
        assert output.status, output.message

        bd1 = db_dao_versioned.get_constraint("bd 1")
        assert bd1.enabled is False
        assert bd1.time_step == BindingConstraintFrequency.WEEKLY
        assert bd1.operator == BindingConstraintOperator.BOTH
        assert bd1.comments == "Hello"  # comments are not updated

        if study_version >= STUDY_VERSION_8_7:
            # Operator changed LESS→BOTH and time step changed HOURLY→WEEKLY:
            # lt and gt tables must exist (reset to weekly zeros), eq must be gone
            db_dao_versioned.get_constraint_less_term_matrix("bd 1")
            db_dao_versioned.get_constraint_greater_term_matrix("bd 1")
            with pytest.raises(BindingConstraintNotFound):
                db_dao_versioned.get_constraint_equal_term_matrix("bd 1")
        else:
            # Pre-8.7: values table still the only one, reset to weekly default
            db_dao_versioned.get_constraint_values_matrix("bd 1")

        if study_version >= STUDY_VERSION_8_7:
            output = UpdateScenarioBuilder(
                data=RulesetUpdate(binding_constraints={"default": {"0": 1}}),
                command_context=command_context,
                study_version=study_version,
            ).apply(study_dao=db_dao_versioned)
            assert output.status, output.message

        output = RemoveMultipleBindingConstraints(
            id="bd 1", command_context=command_context, study_version=study_version
        ).apply(db_dao_versioned)
        assert output.status, output.message

        with pytest.raises(BindingConstraintNotFound):
            db_dao_versioned.get_constraint("bd 1")

        assert "bd 2" in db_dao_versioned.get_all_constraints()

        if study_version >= STUDY_VERSION_8_7:
            # "BD 2" is still present in the "default" group — scenario builder must be untouched
            assert db_dao_versioned.get_ruleset().binding_constraints == {"default": {"0": 1}}

        output = RemoveMultipleBindingConstraints(
            id="bd 2", command_context=command_context, study_version=study_version
        ).apply(db_dao_versioned)
        assert output.status, output.message

        assert db_dao_versioned.get_all_constraints() == {}

        if study_version >= STUDY_VERSION_8_7:
            # "default" group is now empty — scenario builder must be cleaned up
            assert db_dao_versioned.get_ruleset().binding_constraints == {}


def test_scenario_builder(db_dao: DatabaseStudyDao, command_context: CommandContext) -> None:
    """
    Test that the scenario builder is updated when a binding constraint group is renamed or removed.
    """
    study_version = db_dao.get_version()
    assert study_version >= STUDY_VERSION_8_7

    bc_group = "Group 1"
    output = CreateBindingConstraint(
        **{
            "parameters": {
                "name": "BD 1",
                "enabled": False,
                "time_step": BindingConstraintFrequency.DAILY,
                "operator": BindingConstraintOperator.BOTH,
                "group": bc_group,
                "terms": [ConstraintTerm(weight=0.3, data=LinkTerm(area1="area x", area2="area y"))],
            },
            "matrices": {},
            "command_context": command_context,
            "study_version": study_version,
        }
    ).apply(db_dao)
    assert output.status, output.message

    output = UpdateScenarioBuilder(
        data=RulesetUpdate(binding_constraints={bc_group.lower(): {"0": 1}}),
        command_context=command_context,
        study_version=study_version,
    ).apply(study_dao=db_dao)
    assert output.status, output.message

    assert db_dao.get_ruleset().binding_constraints == {"group 1": {"0": 1}}

    # Rename the group — old group's scenario builder rules must be removed
    output = UpdateBindingConstraint(
        **{
            "id": "bd 1",
            "parameters": {"group": "Group 2"},
            "matrices": {},
            "command_context": command_context,
            "study_version": study_version,
        }
    ).apply(db_dao)
    assert output.status, output.message

    assert db_dao.get_ruleset().binding_constraints == {}
