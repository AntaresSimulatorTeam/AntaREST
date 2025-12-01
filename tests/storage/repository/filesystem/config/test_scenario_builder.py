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
import pytest

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.scenario_builder_model import Ruleset, RulesetUpdate
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3
from antarest.study.storage.rawstudy.model.filesystem.config.scenario_builder import (
    parse_ruleset,
    parse_ruleset_update,
    serialize_ruleset,
)


def test_ruleset_parsing_load() -> None:
    rules = {
        "l,be,1": 2,
        "l,be,2": 1,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(load={"be": {"1": 2, "2": 1}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_hydro() -> None:
    rules = {
        "h,be,1": 2,
        "h,be,2": 1,
        "hl,be,1": 0.002,
        "hl,be,2": 0.1,
        "hfl,be,1": 0.4,
        "hfl,be,2": 0.2,
        "hgp,be,1": 10,
        "hgp,be,2": 20,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(
        hydro={"be": {"1": 2, "2": 1}},
        hydro_initial_levels={"be": {"1": 0.2, "2": 10.0}},
        hydro_final_levels={"be": {"1": 40.0, "2": 20.0}},
        hydro_generation_power={"be": {"1": 10, "2": 20}},
    )
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_solar() -> None:
    rules = {
        "s,be,1": 2,
        "s,be,2": 1,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(solar={"be": {"1": 2, "2": 1}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_wind() -> None:
    rules = {
        "w,be,1": 2,
        "w,be,2": 1,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(wind={"be": {"1": 2, "2": 1}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_binding_constraints() -> None:
    rules = {
        "bc,group1,1": 2,
        "bc,group1,2": 1,
        "bc,group2,1": 3,
        "bc,group2,2": 4,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(binding_constraints={"group1": {"1": 2, "2": 1}, "group2": {"1": 3, "2": 4}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_thermal() -> None:
    rules = {
        "t,fr,1,gas": 2,
        "t,fr,2,gas": 1,
        "t,fr,1,nuclear": 1,
        "t,fr,2,nuclear": 2,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(thermal={"fr": {"gas": {"1": 2, "2": 1}, "nuclear": {"1": 1, "2": 2}}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_storages() -> None:
    rules = {
        "sts,fr,1,battery": 2,
        "sts,fr,2,battery": 1,
        "sts,fr,1,cars": 1,
        "sts,fr,2,cars": 2,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(storage_inflows={"fr": {"battery": {"1": 2, "2": 1}, "cars": {"1": 1, "2": 2}}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_renewables() -> None:
    rules = {
        "r,fr,1,solar": 2,
        "r,fr,2,solar": 1,
        "r,fr,1,wind": 1,
        "r,fr,2,wind": 2,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(renewable={"fr": {"solar": {"1": 2, "2": 1}, "wind": {"1": 1, "2": 2}}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_links() -> None:
    rules = {
        "ntc,be,fr,1": 2,
        "ntc,be,fr,2": 1,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(ntc={"be / fr": {"1": 2, "2": 1}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_parsing_storage_constraints() -> None:
    rules = {
        "sta,fr,1,battery1,constraint1": 2,
        "sta,fr,2,battery1,constraint1": 1,
    }
    ruleset = parse_ruleset(rules)
    assert ruleset == Ruleset(storage_constraints={"fr": {"battery1": {"constraint1": {"1": 2, "2": 1}}}})
    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == rules


def test_ruleset_update_parsing_load() -> None:
    rules = {
        "l,be,1": 2,
        "l,be,2": 1,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(load={"be": {"1": 2, "2": 1}})


def test_ruleset_update_parsing_hydro() -> None:
    rules = {
        "h,be,1": 2,
        "h,be,2": 1,
        "hl,be,1": 0.2,
        "hl,be,2": 0.1,
        "hfl,be,1": 0.4,
        "hfl,be,2": 0.2,
        "hgp,be,1": 10,
        "hgp,be,2": 20,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(
        hydro={"be": {"1": 2, "2": 1}},
        hydro_initial_levels={"be": {"1": 20.0, "2": 10.0}},
        hydro_final_levels={"be": {"1": 40.0, "2": 20.0}},
        hydro_generation_power={"be": {"1": 10, "2": 20}},
    )


def test_ruleset_update_parsing_solar() -> None:
    rules = {
        "s,be,1": 2,
        "s,be,2": 1,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(solar={"be": {"1": 2, "2": 1}})


def test_ruleset_update_parsing_wind() -> None:
    rules = {
        "w,be,1": 2,
        "w,be,2": 1,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(wind={"be": {"1": 2, "2": 1}})


def test_ruleset_update_parsing_binding_constraints() -> None:
    rules = {
        "bc,group1,1": 2,
        "bc,group1,2": 1,
        "bc,group2,1": 3,
        "bc,group2,2": 4,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(binding_constraints={"group1": {"1": 2, "2": 1}, "group2": {"1": 3, "2": 4}})


def test_ruleset_update_parsing_thermal() -> None:
    rules = {
        "t,fr,1,gas": 2,
        "t,fr,2,gas": 1,
        "t,fr,1,nuclear": 1,
        "t,fr,2,nuclear": 2,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(thermal={"fr": {"gas": {"1": 2, "2": 1}, "nuclear": {"1": 1, "2": 2}}})


def test_ruleset_update_parsing_storages() -> None:
    rules = {
        "sts,fr,1,battery": 2,
        "sts,fr,2,battery": 1,
        "sts,fr,1,cars": 1,
        "sts,fr,2,cars": 2,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(storage_inflows={"fr": {"battery": {"1": 2, "2": 1}, "cars": {"1": 1, "2": 2}}})


def test_ruleset_update_parsing_renewables() -> None:
    rules = {
        "r,fr,1,solar": 2,
        "r,fr,2,solar": 1,
        "r,fr,1,wind": 1,
        "r,fr,2,wind": 2,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(renewable={"fr": {"solar": {"1": 2, "2": 1}, "wind": {"1": 1, "2": 2}}})


def test_ruleset_update_parsing_links() -> None:
    rules = {
        "ntc,be,fr,1": 2,
        "ntc,be,fr,2": 1,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(ntc={"be / fr": {"1": 2, "2": 1}})


def test_ruleset_update_parsing_storage_constraints() -> None:
    rules = {
        "sta,fr,1,battery1,constraint1": 2,
        "sta,fr,2,battery1,constraint1": 1,
    }
    ruleset = parse_ruleset_update(rules)
    assert ruleset == RulesetUpdate(storage_constraints={"fr": {"battery1": {"constraint1": {"1": 2, "2": 1}}}})


def test_random_is_not_serialized() -> None:
    ruleset = Ruleset(
        load={"fr": {"1": 2, "2": ""}},
        thermal={"fr": {"nuclear": {"1": 2, "2": ""}}},
        ntc={"be / fr": {"1": 2, "2": ""}},
        storage_constraints={"fr": {"battery1": {"constraint1": {"1": 2, "2": ""}}}},
    )

    assert serialize_ruleset(ruleset, STUDY_VERSION_9_3) == {
        "l,fr,1": 2,
        "ntc,be,fr,1": 2,
        "sta,fr,1,battery1,constraint1": 2,
        "t,fr,1,nuclear": 2,
    }


def test_ruleset_serializing_version() -> None:
    rules = {
        "bc,group1,1": 2,
        "bc,group1,2": 1,
        "bc,group2,1": 3,
        "bc,group2,2": 4,
    }
    ruleset = parse_ruleset(rules)
    with pytest.raises(
        InvalidFieldForVersionError, match="Field binding_constraints is not a valid field for study version 8.6"
    ):
        serialize_ruleset(ruleset, STUDY_VERSION_8_6)

    rules = {
        "sta,fr,1,battery1,constraint1": 2,
        "sta,fr,2,battery1,constraint1": 1,
    }
    ruleset = parse_ruleset(rules)
    with pytest.raises(
        InvalidFieldForVersionError, match="Field storage_constraints is not a valid field for study version 9.2"
    ):
        serialize_ruleset(ruleset, STUDY_VERSION_9_2)

    rules = {
        "sts,fr,1,battery": 2,
        "sts,fr,2,battery": 1,
        "sts,fr,1,cars": 1,
        "sts,fr,2,cars": 2,
    }
    ruleset = parse_ruleset(rules)
    with pytest.raises(
        InvalidFieldForVersionError, match="Field storage_inflows is not a valid field for study version 9.2"
    ):
        serialize_ruleset(ruleset, STUDY_VERSION_9_2)

    rules = {
        "hfl,be,1": 0.4,
        "hfl,be,2": 0.2,
    }
    ruleset = parse_ruleset(rules)
    with pytest.raises(
        InvalidFieldForVersionError, match="Field hydro_final_levels is not a valid field for study version 8.8"
    ):
        serialize_ruleset(ruleset, STUDY_VERSION_8_8)
