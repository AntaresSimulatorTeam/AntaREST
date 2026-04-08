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

from collections.abc import Callable
from typing import Any

import pytest

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.scenario_builder_model import (
    Ruleset,
    RulesetUpdate,
    ScenarioType,
    initialize_ruleset_with_version,
    update_ruleset,
)
from antarest.study.business.model.study_index import StudyIndex
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3


def test_ruleset__initialization_from_study() -> None:
    index = StudyIndex(
        areas=["be", "fr"],
        thermals={"be": ["be_therm1", "be_therm2"], "fr": ["fr_therm"]},
        renewables={"be": ["be_renewable1", "be_renewable2"], "fr": ["fr_renewable"]},
        bc_groups=["bc1", "bc2"],
        links=[("be", "fr")],
        storages={"be": [], "fr": ["fr_storage_1", "fr_storage_2"]},
        sts_additional_constraints={"be": {}, "fr": {"fr_storage_1": ["c1", "c2"], "fr_storage_2": []}},
    )

    ruleset = initialize_ruleset_with_version(["1", "2"], index, STUDY_VERSION_9_3)

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

    assert ruleset.storage_constraints == {
        "be": {},
        "fr": {"fr_storage_1": {"c1": expected_mappings, "c2": expected_mappings}, "fr_storage_2": {}},
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
    update.set(scenario_type, {"be": {"1": 2, "2": 1}})  # type: ignore[arg-type]
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)

    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 1}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"2": 3}})  # type: ignore[arg-type]
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 3}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"2": ""}})
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": ""}}


def test_update_ruleset_with_version() -> None:
    # Binding constraints
    error_msg = "Field binding_constraints is not a valid field for study version 8.6"
    ruleset = Ruleset(binding_constraints={"group": {"1": 3}})
    update = RulesetUpdate()
    with pytest.raises(InvalidFieldForVersionError, match=error_msg):
        update_ruleset(ruleset, update, STUDY_VERSION_8_6)

    ruleset = Ruleset()
    update = RulesetUpdate(binding_constraints={"group": {"1": 3}})
    with pytest.raises(InvalidFieldForVersionError, match=error_msg):
        update_ruleset(ruleset, update, STUDY_VERSION_8_6)

    # Hydro final levels
    error_msg = "Field hydro_final_levels is not a valid field for study version 8.8"
    ruleset = Ruleset(hydro_final_levels={"fr": {"1": 0.3}})
    update = RulesetUpdate()
    with pytest.raises(InvalidFieldForVersionError, match=error_msg):
        update_ruleset(ruleset, update, STUDY_VERSION_8_8)

    ruleset = Ruleset()
    update = RulesetUpdate(hydro_final_levels={"fr": {"1": 0.3}})
    with pytest.raises(InvalidFieldForVersionError, match=error_msg):
        update_ruleset(ruleset, update, STUDY_VERSION_8_8)

    # Storage inflows
    for version in [STUDY_VERSION_8_8, STUDY_VERSION_9_2]:
        error_msg = f"Field storage_inflows is not a valid field for study version {version}"
        ruleset = Ruleset(storage_inflows={"fr": {"sts": {"1": 0.3}}})
        update = RulesetUpdate()
        with pytest.raises(InvalidFieldForVersionError, match=error_msg):
            update_ruleset(ruleset, update, version)

        ruleset = Ruleset()
        update = RulesetUpdate(storage_inflows={"fr": {"sts": {"1": 0.3}}})
        with pytest.raises(InvalidFieldForVersionError, match=error_msg):
            update_ruleset(ruleset, update, version)

    # Storage constraints
    for version in [STUDY_VERSION_8_8, STUDY_VERSION_9_2]:
        error_msg = f"Field storage_constraints is not a valid field for study version {version}"
        ruleset = Ruleset(storage_constraints={"fr": {"sts": {"c1": {"1": 0.3}}}})
        update = RulesetUpdate()
        with pytest.raises(InvalidFieldForVersionError, match=error_msg):
            update_ruleset(ruleset, update, version)

        ruleset = Ruleset()
        update = RulesetUpdate(storage_constraints={"fr": {"sts": {"c1": {"1": 0.3}}}})
        with pytest.raises(InvalidFieldForVersionError, match=error_msg):
            update_ruleset(ruleset, update, version)


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
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)

    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": 1}}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"item1": {"2": 3}, "item2": {"1": 2, "2": 1}}})
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": 3}, "item2": {"1": 2, "2": 1}}}

    update = RulesetUpdate()
    update.set(scenario_type, {"be": {"item1": {"2": ""}}})
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.get(scenario_type) == {"be": {"item1": {"1": 2, "2": ""}, "item2": {"1": 2, "2": 1}}}


def test_update_ruleset_3_levels_scenarios() -> None:
    mapping = {"1": 2, "2": 1}
    ruleset = Ruleset()
    update = RulesetUpdate()
    update.storage_constraints = {"be": {"storage1": {"c1": mapping}}}
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)

    assert update.storage_constraints == {"be": {"storage1": {"c1": mapping}}}

    update = RulesetUpdate()
    update.storage_constraints = {"be": {"storage1": {"c1": {"2": 3}}}}
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.storage_constraints == {"be": {"storage1": {"c1": {"1": 2, "2": 3}}}}

    update = RulesetUpdate()
    update.storage_constraints = {"be": {"storage1": {"c1": {"2": ""}}}}
    update_ruleset(ruleset, update, STUDY_VERSION_9_3)
    assert ruleset.storage_constraints == {"be": {"storage1": {"c1": {"1": 2, "2": ""}}}}


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
        (ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS, lambda r: r.storage_constraints),
    ],
)
def test_get_set_by_type(
    ruleset_cls: type[Ruleset | RulesetUpdate],
    scenario_type: ScenarioType,
    getter: Callable[[Any], Any],
) -> None:
    ruleset = ruleset_cls()
    ruleset.set(scenario_type, {"be": {"1": 2, "2": 1}})  # type: ignore[arg-type]
    assert getter(ruleset) == {"be": {"1": 2, "2": 1}}
    assert ruleset.get(scenario_type) == {"be": {"1": 2, "2": 1}}


@pytest.mark.parametrize("ruleset_cls", [Ruleset, RulesetUpdate])
@pytest.mark.parametrize(
    "scenario_type,getter",
    [
        (ScenarioType.RENEWABLE, lambda r: r.renewable),
        (ScenarioType.THERMAL, lambda r: r.thermal),
        (ScenarioType.SHORT_TERM_STORAGE_INFLOWS, lambda r: r.storage_inflows),
    ],
)
def test_get_set_by_type_2_levels(
    ruleset_cls: type[Ruleset | RulesetUpdate],
    scenario_type: ScenarioType,
    getter: Callable[[Any], Any],
) -> None:
    ruleset = ruleset_cls()
    ruleset.set(scenario_type, {"be": {"cluster": {"1": 2, "2": 1}}})
    assert getter(ruleset) == {"be": {"cluster": {"1": 2, "2": 1}}}
    assert ruleset.get(scenario_type) == {"be": {"cluster": {"1": 2, "2": 1}}}


@pytest.mark.parametrize("ruleset_cls", [Ruleset, RulesetUpdate])
def test_get_set_by_type_storage_constraints(ruleset_cls: type[Ruleset | RulesetUpdate]) -> None:
    mapping = {"be": {"storage": {"c1": {"1": 2, "2": 1}}}}
    ruleset = ruleset_cls()
    ruleset.set(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS, mapping)
    assert ruleset.storage_constraints == mapping
    assert ruleset.get(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS) == mapping
