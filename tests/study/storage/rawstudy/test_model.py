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
from unittest.mock import Mock

from antarest.study.business.model.binding_constraint_model import BindingConstraintFrequency, BindingConstraintOperator
from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintConfig, FileStudyTreeConfig


def test_binding_constraints_groups_before_8_6() -> None:
    bc_config = BindingConstraintConfig(
        id="bc_id",
        name="bc_name",
        enabled=True,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.LESS,
    )

    # In v8.6, binding constraints did not have groups
    fs = FileStudyTreeConfig(
        study_path=Mock(), path=Mock(), study_id="study_id", version=STUDY_VERSION_8_6, bindings=[bc_config]
    )

    assert fs.get_binding_constraint_groups() == []


def test_binding_constraints_groups_after_8_6() -> None:
    bc_config = BindingConstraintConfig(
        id="bc_id",
        name="bc_name",
        enabled=True,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.LESS,
        group="group_id",
    )

    # In v8.6, binding constraints did not have groups
    fs = FileStudyTreeConfig(
        study_path=Mock(), path=Mock(), study_id="study_id", version=STUDY_VERSION_8_6, bindings=[bc_config]
    )

    assert fs.get_binding_constraint_groups() == ["group_id"]
