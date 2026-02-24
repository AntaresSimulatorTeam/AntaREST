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
Unit tests for DatabaseScenarioBuilderDAO.
"""

import pytest

from antarest.core.exceptions import RulesetNotFound
from antarest.study.business.model.scenario_builder_model import Ruleset, ScenarioType
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_get_active_ruleset_returns_default_when_empty(dao: DatabaseStudyDao) -> None:
    assert dao.get_active_ruleset_name() == "Default Ruleset"


def test_save_then_get_active_ruleset_name(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder({"my_ruleset": Ruleset()})
    dao.save_active_ruleset_name("my_ruleset")
    assert dao.get_active_ruleset_name() == "my_ruleset"


def test_save_active_ruleset_overwrites_previous(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder({"first": Ruleset(), "second": Ruleset()})
    dao.save_active_ruleset_name("first")
    dao.save_active_ruleset_name("second")
    assert dao.get_active_ruleset_name() == "second"


def test_save_empty_rulesets(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder({})
    assert dao.get_rulesets() == {}


def test_save_ruleset_with_area_scenarios(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "R1": Ruleset(
            load={"fr": {"0": 1, "1": 2}},
            wind={"de": {"0": 3}},
        )
    }
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].load == {"fr": {"0": 1, "1": 2}}
    assert result["R1"].wind == {"de": {"0": 3}}


def test_save_ruleset_with_link_scenarios(dao: DatabaseStudyDao) -> None:
    rulesets = {"R1": Ruleset(ntc={"fr - de": {"0": 1, "1": 2}})}
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].ntc == {"fr - de": {"0": 1, "1": 2}}


def test_save_ruleset_with_binding_constraints(dao: DatabaseStudyDao) -> None:
    rulesets = {"R1": Ruleset(binding_constraints={"group1": {"0": 5, "1": 6}})}
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].binding_constraints == {"group1": {"0": 5, "1": 6}}


def test_save_ruleset_with_area_item_scenarios(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "R1": Ruleset(
            thermal={"fr": {"gas_cluster": {"0": 1, "1": 2}}},
            renewable={"de": {"wind_farm": {"0": 3}}},
        )
    }
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].thermal == {"fr": {"gas_cluster": {"0": 1, "1": 2}}}
    assert result["R1"].renewable == {"de": {"wind_farm": {"0": 3}}}


def test_save_ruleset_with_storage_inflows(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "R1": Ruleset(
            storage_inflows={"fr": {"battery_1": {"0": 4, "1": 5}}},
        )
    }
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].storage_inflows == {"fr": {"battery_1": {"0": 4, "1": 5}}}


def test_save_ruleset_with_storage_constraints(dao: DatabaseStudyDao) -> None:
    rulesets = {"R1": Ruleset(storage_constraints={"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}})}
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert result["R1"].storage_constraints == {"fr": {"battery": {"constraint_a": {"0": 10, "1": 20}}}}


def test_save_multiple_rulesets(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "winter": Ruleset(load={"fr": {"0": 1}}),
        "summer": Ruleset(load={"fr": {"0": 99}}),
    }
    dao.save_scenario_builder(rulesets)
    result = dao.get_rulesets()

    assert set(result.keys()) == {"winter", "summer"}
    assert result["winter"].load == {"fr": {"0": 1}}
    assert result["summer"].load == {"fr": {"0": 99}}


def test_save_replaces_previous_rulesets(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder({"old": Ruleset(load={"fr": {"0": 1}})})
    dao.save_scenario_builder({"new": Ruleset(wind={"de": {"0": 2}})})
    result = dao.get_rulesets()

    assert "old" not in result
    assert result["new"].wind == {"de": {"0": 2}}


def test_save_replaces_active_ruleset_via_cascade(dao: DatabaseStudyDao) -> None:
    dao.save_scenario_builder({"R1": Ruleset()})
    dao.save_active_ruleset_name("R1")

    # Overwrite rulesets entirely — R1 no longer exists
    dao.save_scenario_builder({"R2": Ruleset()})

    # Active ruleset should have been deleted by cascade
    assert dao.get_active_ruleset_name() == "Default Ruleset"


def test_save_active_ruleset_name_with_nonexistent_ruleset_raises(dao: DatabaseStudyDao) -> None:
    with pytest.raises(RulesetNotFound):
        dao.save_active_ruleset_name("nonexistent")


def test_get_scenario_by_type_area(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset(load={"fr": {"0": 1}, "de": {"0": 2}})}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.LOAD)
    assert result == {"fr": {"0": 1}, "de": {"0": 2}}


def test_get_scenario_by_type_link(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset(ntc={"fr - de": {"0": 7}})}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.LINK)
    assert result == {"fr - de": {"0": 7}}


def test_get_scenario_by_type_area_item(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset(thermal={"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}})}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.THERMAL)
    assert result == {"fr": {"gas": {"0": 1}, "nuc": {"0": 2}}}


def test_get_scenario_by_type_storage_inflows(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset(storage_inflows={"fr": {"battery_1": {"0": 4}}})}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert result == {"fr": {"battery_1": {"0": 4}}}


def test_get_scenario_by_type_storage_constraints(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset(storage_constraints={"fr": {"battery": {"c1": {"0": 10}}}})}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_ADDITIONAL_CONSTRAINTS)
    assert result == {"fr": {"battery": {"c1": {"0": 10}}}}


def test_get_scenario_by_type_returns_empty_when_no_data(dao: DatabaseStudyDao) -> None:
    rulesets = {"active": Ruleset()}
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.SOLAR)
    assert result == {}


def test_get_scenario_by_type_only_returns_active_ruleset(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "active": Ruleset(load={"fr": {"0": 1}}),
        "other": Ruleset(load={"de": {"0": 99}}),
    }
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    result = dao.get_scenario_by_type(ScenarioType.LOAD)
    assert result == {"fr": {"0": 1}}


def test_get_scenario_by_type_does_not_mix_scenario_types(dao: DatabaseStudyDao) -> None:
    rulesets = {
        "active": Ruleset(
            load={"fr": {"0": 1}},
            wind={"fr": {"0": 99}},
        )
    }
    dao.save_scenario_builder(rulesets)
    dao.save_active_ruleset_name("active")

    assert dao.get_scenario_by_type(ScenarioType.LOAD) == {"fr": {"0": 1}}
    assert dao.get_scenario_by_type(ScenarioType.WIND) == {"fr": {"0": 99}}
