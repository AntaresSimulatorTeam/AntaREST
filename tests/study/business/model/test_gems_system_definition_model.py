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

from antarest.core.exceptions import GemsInvalidParameterValue
from antarest.study.business.model.gems.system import GemsComponent


@pytest.mark.parametrize(
    "value, time_dependent, scenario_dependent, value_in_message",
    [
        (42, True, False, "42.0"),  # time-dependent, int value
        (3.14, False, True, "3.14"),  # scenario-dependent, float value
        (2.718, True, True, "2.718"),  # time and scenario-dependent, float value
    ],
)
def test_parameter_value_raises_when_float_and_value_depends_on_time_or_scenario(
    value: float, time_dependent: bool, scenario_dependent: bool, value_in_message: str
) -> None:
    with pytest.raises(
        GemsInvalidParameterValue,
        match=re.escape(
            f"Time and/or scenario-dependent parameters must have a string value (path to CSV file), "
            f"but {value_in_message} was given for param1 parameter"
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
        GemsInvalidParameterValue,
        match=re.escape("Constant parameters must have a numeric value, but 'test' was given for param1 parameter"),
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

    assert component is not None
