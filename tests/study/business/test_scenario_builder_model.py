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

from antarest.study.business.model.scenario_builder_model import (
    Ruleset,
    RulesetUpdate,
    ScenarioType,
    initialize_ruleset,
    update_ruleset,
)
from antarest.study.business.model.study_index import StudyIndex


def test_ruleset__initialization_from_study() -> None:
    index = StudyIndex(
        areas=["be", "fr"],
        thermals={"be": ["be_therm1", "be_therm2"], "fr": ["fr_therm"]},
        renewables={"be": ["be_renewable1", "be_renewable2"], "fr": ["fr_renewable"]},
        bc_groups=["bc1", "bc2"],
        links=[("be", "fr")],
        storages={"be": [], "fr": ["fr_storage_1", "fr_storage_2"]},
    )

    ruleset = initialize_ruleset(["1", "2"], index)

    # expect RAND value for each year
    expected_mappings = {"1": "", "2": ""}
    expected_area_mappings = {"be": expected_mappings, "fr": expected_mappings}
    assert ruleset.load == expected_area_mappings
    assert ruleset.hydro == expected_area_mappings
    assert ruleset.hydro_initial_levels == expected_area_mappings
    assert ruleset.hydro_final_levels == expected_area_mappings
    assert ruleset.hydro_generation_power == expected_area_mappings
    assert ruleset.solar == expected_area_mappings
    assert ruleset.wind == expected_area_mappings

    assert ruleset.binding_constraints == {"bc1": expected_mappings, "bc2": expected_mappings}

    assert ruleset.ntc == {"be / fr": expected_mappings}

    assert ruleset.thermal == {
        "be": {"be_therm1": expected_mappings, "be_therm2": expected_mappings},
        "fr": {"fr_therm": expected_mappings},
    }
    assert ruleset.renewable == {
        "be": {"be_renewable1": expected_mappings, "be_renewable2": expected_mappings},
        "fr": {"fr_renewable": expected_mappings},
    }

    assert ruleset.storage_inflows == {
        "be": {},
        "fr": {"fr_storage_1": expected_mappings, "fr_storage_2": expected_mappings},
    }


@pytest.mark.parametrize(
    "scenario_type",
    [
        ScenarioType.LOAD,
        ScenarioType.HYDRO,
        ScenarioType.HYDRO_INITIAL_LEVEL,
        ScenarioType.HYDRO_FINAL_LEVEL,
        ScenarioType.HYDRO_GENERATION_POWER,
        ScenarioType.SOLAR,
        ScenarioType.WIND,
        ScenarioType.BINDING_CONSTRAINTS,
        ScenarioType.LINK,
    ],
)
def test_update_ruleset_simple_scenarios(scenario_type: ScenarioType) -> None:
    ruleset = Ruleset()
    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"1": 2, "2": 1}})
    update_ruleset(ruleset, update)

    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 1}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"2": 3}})
    update_ruleset(ruleset, update)
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 3}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"2": ""}})
    update_ruleset(ruleset, update)
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": ""}}


@pytest.mark.parametrize(
    "scenario_type",
    [
        ScenarioType.THERMAL,
        ScenarioType.RENEWABLE,
        ScenarioType.SHORT_TERM_STORAGE_INFLOWS,
    ],
)
def test_update_ruleset_2_levels_scenarios(scenario_type: ScenarioType) -> None:
    ruleset = Ruleset()
    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"item1": {"1": 2, "2": 1}}})
    update_ruleset(ruleset, update)

    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": 1}}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"item1": {"2": 3}, "item2": {"1": 2, "2": 1}}})
    update_ruleset(ruleset, update)
    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": 3}, "item2": {"1": 2, "2": 1}}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"item1": {"2": ""}}})
    update_ruleset(ruleset, update)
    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": ""}, "item2": {"1": 2, "2": 1}}}


@pytest.mark.parametrize("ruleset_cls", [Ruleset, RulesetUpdate])
@pytest.mark.parametrize(
    "scenario_type,getter",
    [
        (ScenarioType.LOAD, lambda r: r.load),
        (ScenarioType.HYDRO, lambda r: r.hydro),
        (ScenarioType.HYDRO_INITIAL_LEVEL, lambda r: r.hydro_initial_levels),
        (ScenarioType.HYDRO_FINAL_LEVEL, lambda r: r.hydro_final_levels),
        (ScenarioType.HYDRO_GENERATION_POWER, lambda r: r.hydro_generation_power),
        (ScenarioType.SOLAR, lambda r: r.solar),
        (ScenarioType.WIND, lambda r: r.wind),
        (ScenarioType.BINDING_CONSTRAINTS, lambda r: r.binding_constraints),
        (ScenarioType.LINK, lambda r: r.ntc),
    ],
)
def test_get_set_by_type(ruleset_cls, scenario_type: ScenarioType, getter) -> None:
    ruleset = ruleset_cls()
    ruleset.set(scenario_type, {"be": {"1": 2, "2": 1}})
    assert getter(ruleset) == {"be": {"1": 2, "2": 1}}
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 1}}
