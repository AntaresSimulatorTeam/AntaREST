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
import pytest

from antarest.study.business.scenario_builder_management import Ruleset, Rulesets, parse_rulesets, serialize_rulesets


@pytest.fixture
def rulesets() -> Rulesets:
    ruleset = Ruleset()

    ruleset.load = {"fr": {"1": 10, "2": 20}, "be": {"1": 5, "2": 1}}
    ruleset.thermal = {"ch": {"nuclear": {"1": 10, "2": 20}, "gas": {"1": 5, "2": 1}}}
    ruleset.hydro = {"at": {"5": 10}}
    ruleset.hydro_initial_levels = {"at": {"10": 12}}
    ruleset.hydro_final_levels = {"at": {"20": 32}}
    ruleset.hydro_generation_power = {"at": {"25": 15}}
    ruleset.renewable = {"ch": {"wind1": {"1": 10}, "solar2": {"1": 5}}}
    ruleset.ntc = {"be / fr": {"1": 10, "2": 20}}
    ruleset.binding_constraints = {"bc1": {"1": 10, "2": 20}}
    ruleset.storage_inflows = {"ch": {"storage1": {"1": 10, "2": 20}, "storage2": {"1": 5, "2": 1}}}
    ruleset.storage_constraints = {"fr": {"battery": {"constraint1": {"1": 220}, "constraint2": {"1": 55}}}}
    ruleset.solar = {"fr": {"1": 110}}
    ruleset.wind = {"fr": {"1": 220}}
    return {"rules1": ruleset}


@pytest.fixture
def serialized_rulesets() -> dict[str, dict[str, int]]:
    return {
        "rules1": {
            # load
            "l,fr,1": 10,
            "l,fr,2": 20,
            "l,be,1": 5,
            "l,be,2": 1,
            # thermal
            "t,ch,1,nuclear": 10,
            "t,ch,2,nuclear": 20,
            "t,ch,1,gas": 5,
            "t,ch,2,gas": 1,
            # hydro
            "h,at,5": 10,
            # hydro initial levels
            "hl,at,10": 0.12,
            # hydro final levels
            "hfl,at,20": 0.32,
            # hydro generation power
            "hgp,at,25": 15,
            # renewable
            "r,ch,1,wind1": 10,
            "r,ch,1,solar2": 5,
            # NTCs
            "ntc,be,fr,1": 10,
            "ntc,be,fr,2": 20,
            # BCs
            "bc,bc1,1": 10,
            "bc,bc1,2": 20,
            # solar
            "s,fr,1": 110,
            # wind
            "w,fr,1": 220,
            # STS
            "sts,ch,1,storage1": 10,
            "sts,ch,2,storage1": 20,
            "sts,ch,1,storage2": 5,
            "sts,ch,2,storage2": 1,
            # STS constraints
            "sta,fr,1,battery,constraint1": 220,
            "sta,fr,1,battery,constraint2": 55,
        }
    }


def test_scenario_builder_serialization(rulesets: Rulesets, serialized_rulesets: dict[str, dict[str, int]]) -> None:
    assert serialize_rulesets(rulesets) == serialized_rulesets


def test_scenario_builder_parsing(rulesets: Rulesets, serialized_rulesets: dict[str, dict[str, int]]):
    assert parse_rulesets(serialized_rulesets) == rulesets
