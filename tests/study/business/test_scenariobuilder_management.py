# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from antarest.study.business.scenario_builder_management import Ruleset, serialize_rulesets


def test_scenario_builder_parsing():
    pass


def test_scenario_builder_serialization():
    ruleset = Ruleset()
    ruleset.load = {"fr": {"1": 10, "2": 20}}
    res = serialize_rulesets({"rules1": ruleset})
    assert res == {"rules1": {"l": {"1": 10, "2": 20}}}
