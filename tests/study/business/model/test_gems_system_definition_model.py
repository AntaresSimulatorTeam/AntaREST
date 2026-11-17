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
import re

import pytest
from pydantic import ValidationError

from antarest.core.exceptions import (
    GemsParameterValueIsConstantButShouldNotBe,
    GemsParameterValueIsNotConstantButShouldBe,
)
from antarest.study.business.model.gems.system import GemsComponent


@pytest.mark.parametrize(
    "value, time_dependent, scenario_dependent",
    [
        (42, True, False),  # time-dependent, int value
        (3.14, False, True),  # scenario-dependent, float value
        (2.718, True, True),  # time and scenario-dependent, float value
    ],
)
def test_parameter_value_raises_when_float_and_value_depends_on_time_or_scenario(
    value: float, time_dependent: bool, scenario_dependent: bool
) -> None:
    with pytest.raises(
        GemsParameterValueIsConstantButShouldNotBe,
        match=re.escape(
            f"Parameter 'param1' had this constant value: {float(value)} but should be time and/or scenario dependent"
        ),
    ):
        GemsComponent.model_validate(
            {
                "id": "dsr",
                "model": "andromede-v1-models-weo-hybrid.dsr",
                "parameters": [
                    {
                        "id": "param1",
                        "time-dependent": time_dependent,
                        "scenario-dependent": scenario_dependent,
                        "value": value,
                    },
                ],
            }
        )


def test_parameter_raises_when_value_is_a_string_and_value_does_not_depend_on_time_or_scenario() -> None:

    with pytest.raises(
        GemsParameterValueIsNotConstantButShouldBe,
        match="Parameter 'param1' had this value: 'test' but should be constant",
    ):
        GemsComponent.model_validate(
            {
                "id": "dsr",
                "model": "andromede-v1-models-weo-hybrid.dsr",
                "parameters": [
                    {
                        "id": "param1",
                        "time-dependent": False,
                        "scenario-dependent": False,
                        "value": "test",
                    },
                ],
            }
        )


@pytest.mark.parametrize(
    "value, time_dependent, scenario_dependent",
    [
        ("demand_profile_1", True, False),
        ("demand_profile_2", False, True),
        ("demand_profile_3", True, True),
        (42, False, False),
    ],
)
def test_parameter_value_should_not_raise_when_properly_filled(
    value: float | str, time_dependent: bool, scenario_dependent: bool
) -> None:

    component = GemsComponent.model_validate(
        {
            "id": "dsr",
            "model": "andromede-v1-models-weo-hybrid.dsr",
            "parameters": [
                {
                    "id": "param1",
                    "time-dependent": time_dependent,
                    "scenario-dependent": scenario_dependent,
                    "value": value,
                },
            ],
        }
    )

    assert component.id == "dsr"
    assert component.model == "andromede-v1-models-weo-hybrid.dsr"
    assert component.parameters[0].id == "param1"
    assert component.parameters[0].time_dependent == time_dependent
    assert component.parameters[0].scenario_dependent == scenario_dependent
    assert component.parameters[0].value == value


def test_integer_strategy() -> None:
    with pytest.raises(ValidationError, match="heuristic-id is required when id is 'heuristic'"):
        GemsComponent.model_validate({"id": "id", "model": "model", "integer-strategy": {"id": "heuristic"}})

    with pytest.raises(ValidationError, match="heuristic-id is forbidden when id is not 'heuristic'"):
        GemsComponent.model_validate(
            {"id": "id", "model": "model", "integer-strategy": {"id": "relaxed", "heuristic-id": "fast"}}
        )

    # Wrong enum values
    with pytest.raises(ValidationError, match="Input should be 'exact', 'relaxed' or 'heuristic'"):
        GemsComponent.model_validate({"id": "id", "model": "model", "integer-strategy": {"id": "wrong id"}})

    with pytest.raises(ValidationError, match="Input should be 'fast' or 'accurate'"):
        GemsComponent.model_validate(
            {"id": "id", "model": "model", "integer-strategy": {"id": "heuristic", "heuristic-id": "wrong id"}}
        )
