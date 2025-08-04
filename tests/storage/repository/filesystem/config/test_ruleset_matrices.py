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

import typing as t

import numpy as np
import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.ruleset_matrices import RulesetMatrices, TableForm

SCENARIO_TYPES = {
    "l": "load",
    "h": "hydro",
    "w": "wind",
    "s": "solar",
    "t": "thermal",
    "r": "renewable",
    "ntc": "link",
    "bc": "bindingConstraints",
    "hl": "hydroInitialLevels",
    "hfl": "hydroFinalLevels",
    "hgp": "hydroGenerationPower",
    "sts": "shortTermStorage",
}


@pytest.fixture(name="ruleset")
def ruleset_fixture() -> RulesetMatrices:
    return RulesetMatrices(
        nb_years=4,
        areas=["France", "Germany", "Italy"],
        links=[("Germany", "France"), ("Italy", "France")],
        thermals={"France": ["nuclear", "coal"], "Italy": ["nuclear", "fuel"], "Germany": ["gaz", "fuel"]},
        renewables={"France": ["wind offshore", "wind onshore"], "Germany": ["wind onshore"]},
        groups=["Main", "Secondary"],
        scenario_types=SCENARIO_TYPES,
    )


class TestRulesetMatrices:
    def test_ruleset__init(self, ruleset: RulesetMatrices) -> None:
        assert ruleset.columns == ["0", "1", "2", "3"]
        assert ruleset.scenarios["load"].shape == (3, 4)
        assert ruleset.scenarios["load"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["hydro"].shape == (3, 4)
        assert ruleset.scenarios["hydro"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["wind"].shape == (3, 4)
        assert ruleset.scenarios["wind"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["solar"].shape == (3, 4)
        assert ruleset.scenarios["solar"].index.tolist() == ["France", "Germany", "Italy"]
        thermal = ruleset.scenarios["thermal"]
        assert thermal["France"].shape == (2, 4)
        assert thermal["France"].index.tolist() == ["nuclear", "coal"]
        assert thermal["Italy"].shape == (2, 4)
        assert thermal["Italy"].index.tolist() == ["nuclear", "fuel"]
        assert thermal["Germany"].shape == (2, 4)
        renewable = ruleset.scenarios["renewable"]
        assert renewable["France"].shape == (2, 4)
        assert renewable["France"].index.tolist() == ["wind offshore", "wind onshore"]
        assert renewable["Germany"].shape == (1, 4)
        assert renewable["Germany"].index.tolist() == ["wind onshore"]
        assert ruleset.scenarios["link"].shape == (2, 4)
        assert ruleset.scenarios["link"].index.tolist() == ["Germany / France", "Italy / France"]
        assert ruleset.scenarios["bindingConstraints"].shape == (2, 4)
        assert ruleset.scenarios["bindingConstraints"].index.tolist() == ["Main", "Secondary"]
        assert ruleset.scenarios["hydroInitialLevels"].shape == (3, 4)
        assert ruleset.scenarios["hydroInitialLevels"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["hydroFinalLevels"].shape == (3, 4)
        assert ruleset.scenarios["hydroFinalLevels"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["hydroGenerationPower"].shape == (3, 4)
        assert ruleset.scenarios["hydroGenerationPower"].index.tolist() == ["France", "Germany", "Italy"]
        assert ruleset.scenarios["shortTermStorage"].shape == (3, 4)
        assert ruleset.scenarios["shortTermStorage"].index.tolist() == ["France", "Germany", "Italy"]

    @pytest.mark.parametrize(
        "symbol, scenario_type",
        [
            ("l", "load"),
            ("h", "hydro"),
            ("w", "wind"),
            ("s", "solar"),
            ("hgp", "hydroGenerationPower"),
            ("sts", "shortTermStorage"),
        ],
    )
    def test_update_rules__load(self, ruleset: RulesetMatrices, symbol: str, scenario_type: str) -> None:
        rules = {
            f"{symbol},france,0": 1,
            f"{symbol},germany,0": 2,
            f"{symbol},italy,0": 3,
            f"{symbol},france,1": 4,
            f"{symbol},germany,1": 5,
            f"{symbol},italy,1": 6,
            f"{symbol},france,2": 7,
            f"{symbol},germany,2": 8,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios[scenario_type]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 1, "1": 4, "2": 7, "3": "NaN"},
            "Germany": {"0": 2, "1": 5, "2": 8, "3": "NaN"},
            "Italy": {"0": 3, "1": 6, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__link(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "ntc,germany,france,0": 1,
            "ntc,italy,france,0": 2,
            "ntc,germany,france,1": 3,
            "ntc,italy,france,1": 4,
            "ntc,germany,france,2": 5,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["link"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "Germany / France": {"0": 1, "1": 3, "2": 5, "3": "NaN"},
            "Italy / France": {"0": 2, "1": 4, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__thermal(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "t,france,0,nuclear": 1,
            "t,france,0,coal": 2,
            "t,italy,0,nuclear": 3,
            "t,italy,0,fuel": 4,
            "t,france,1,nuclear": 5,
            "t,france,1,coal": 6,
            "t,italy,1,nuclear": 7,
            "t,italy,1,fuel": 8,
        }
        ruleset.update_rules(rules)
        actual_map = ruleset.scenarios["thermal"]

        actual = actual_map["France"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "coal": {"0": 2, "1": 6, "2": "NaN", "3": "NaN"},
            "nuclear": {"0": 1, "1": 5, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual = actual_map["Italy"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "fuel": {"0": 4, "1": 8, "2": "NaN", "3": "NaN"},
            "nuclear": {"0": 3, "1": 7, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual = actual_map["Germany"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "gaz": {"0": "NaN", "1": "NaN", "2": "NaN", "3": "NaN"},
            "fuel": {"0": "NaN", "1": "NaN", "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__renewable(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "r,france,0,wind offshore": 1,
            "r,france,0,wind onshore": 2,
            "r,germany,0,wind onshore": 3,
            "r,france,1,wind offshore": 4,
            "r,france,1,wind onshore": 5,
            "r,germany,1,wind onshore": 6,
        }
        ruleset.update_rules(rules)
        actual_map = ruleset.scenarios["renewable"]

        actual = actual_map["France"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "wind offshore": {"0": 1, "1": 4, "2": "NaN", "3": "NaN"},
            "wind onshore": {"0": 2, "1": 5, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual = actual_map["Germany"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "wind onshore": {"0": 3, "1": 6, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__hydro(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "h,france,0": 1,
            "h,germany,0": 2,
            "h,italy,0": 3,
            "h,france,1": 4,
            "h,germany,1": 5,
            "h,italy,1": 6,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["hydro"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 1, "1": 4, "2": "NaN", "3": "NaN"},
            "Germany": {"0": 2, "1": 5, "2": "NaN", "3": "NaN"},
            "Italy": {"0": 3, "1": 6, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__hydro_generation_power(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "hgp,france,0": 1,
            "hgp,germany,0": 2,
            "hgp,italy,0": 3,
            "hgp,france,1": 4,
            "hgp,germany,1": 5,
            "hgp,italy,1": 6,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["hydroGenerationPower"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 1, "1": 4, "2": "NaN", "3": "NaN"},
            "Germany": {"0": 2, "1": 5, "2": "NaN", "3": "NaN"},
            "Italy": {"0": 3, "1": 6, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__short_term_storage(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "sts,france,0": 1,
            "sts,germany,0": 2,
            "sts,italy,0": 3,
            "sts,france,1": 4,
            "sts,germany,1": 5,
            "sts,italy,1": 6,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["shortTermStorage"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 1, "1": 4, "2": "NaN", "3": "NaN"},
            "Germany": {"0": 2, "1": 5, "2": "NaN", "3": "NaN"},
            "Italy": {"0": 3, "1": 6, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__binding_constraints(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "bc,main,0": 1,
            "bc,secondary,0": 2,
            "bc,main,1": 3,
            "bc,secondary,1": 4,
            "bc,main,2": 5,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["bindingConstraints"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "Main": {"0": 1, "1": 3, "2": 5, "3": "NaN"},
            "Secondary": {"0": 2, "1": 4, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, int)

    def test_update_rules__hydro_initial_levels(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "hl,france,0": 0.1,
            "hl,germany,0": 0.2,
            "hl,italy,0": 0.3,
            "hl,france,1": 0.4537,
            "hl,germany,1": 0.5,
            "hl,italy,1": 0.6,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["hydroInitialLevels"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 10, "1": 45.37, "2": "NaN", "3": "NaN"},
            "Germany": {"0": 20, "1": 50, "2": "NaN", "3": "NaN"},
            "Italy": {"0": 30, "1": 60, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules
        for rule_id, ts_number in actual_rules.items():
            assert isinstance(ts_number, float)

    def test_update_rules__hydro_final_levels(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "hfl,france,0": 0.1,
            "hfl,germany,0": 0.2,
            "hfl,italy,0": 0.3,
            "hfl,france,1": 0.4,
            "hfl,germany,1": 0.5,
            "hfl,italy,1": 0.6,
        }
        ruleset.update_rules(rules)
        actual = ruleset.scenarios["hydroFinalLevels"]
        actual = actual.fillna("NaN").to_dict(orient="index")
        expected = {
            "France": {"0": 10, "1": 40, "2": "NaN", "3": "NaN"},
            "Germany": {"0": 20, "1": 50, "2": "NaN", "3": "NaN"},
            "Italy": {"0": 30, "1": 60, "2": "NaN", "3": "NaN"},
        }
        assert actual == expected

        actual_rules = ruleset.get_rules()
        assert actual_rules == rules

    def test_update_rules__invalid(self, ruleset: RulesetMatrices) -> None:
        rules = {
            "invalid,france,0": 1,
            "invalid,germany,0": 2,
            "invalid,italy,0": 3,
            "invalid,france,1": 4,
            "invalid,germany,1": 5,
            "invalid,italy,1": 6,
        }
        with pytest.raises(KeyError):
            ruleset.update_rules(rules)
        assert ruleset.get_rules() == {}

    def test_set_table_form(self, ruleset: RulesetMatrices) -> None:
        table_form = {
            "load": {
                "France": {"0": 1, "1": 2, "2": 3, "3": 4},
                "Germany": {"0": 5, "1": 6, "2": 7, "3": 8},
                "Italy": {"0": 9, "1": "", "2": "", "3": ""},
            },
            "hydro": {
                "France": {"0": 5, "1": 6, "2": "", "3": 8},
                "Germany": {"0": 9, "1": 10, "2": 11, "3": 12},
                "Italy": {"0": 13, "1": "", "2": 15, "3": 16},
            },
            "wind": {
                "France": {"0": 17, "1": 18, "2": 19, "3": 20},
                "Germany": {"0": 21, "1": 22, "2": 23, "3": 24},
                "Italy": {"0": 25, "1": 26, "2": 27, "3": 28},
            },
            "solar": {
                "France": {"0": 29, "1": 30, "2": 31, "3": 32},
                "Germany": {"0": 33, "1": 34, "2": 35, "3": 36},
                "Italy": {"0": 37, "1": 38, "2": 39, "3": 40},
            },
            "thermal": {
                "France": {
                    "nuclear": {"0": 41, "1": 42, "2": 43, "3": 44},
                    "coal": {"0": 45, "1": 46, "2": 47, "3": 48},
                },
                "Germany": {
                    "gaz": {"0": 49, "1": 50, "2": 51, "3": 52},
                    "fuel": {"0": 53, "1": 54, "2": 55, "3": 56},
                },
                "Italy": {
                    "nuclear": {"0": 57, "1": 58, "2": 59, "3": 60},
                    "fuel": {"0": 61, "1": 62, "2": 63, "3": 64},
                },
            },
            "renewable": {
                "France": {
                    "wind offshore": {"0": 65, "1": 66, "2": 67, "3": 68},
                    "wind onshore": {"0": 69, "1": 70, "2": 71, "3": 72},
                },
                "Germany": {
                    "wind onshore": {"0": 73, "1": 74, "2": 75, "3": 76},
                },
            },
            "link": {
                "Germany / France": {"0": 77, "1": 78, "2": 79, "3": 80},
                "Italy / France": {"0": 81, "1": 82, "2": 83, "3": 84},
            },
            "bindingConstraints": {
                "Main": {"0": 85, "1": 86, "2": 87, "3": 88},
                "Secondary": {"0": 89, "1": 90, "2": 91, "3": 92},
            },
            "hydroInitialLevels": {
                "France": {"0": 93, "1": 94, "2": 95, "3": 96},
                "Germany": {"0": 97, "1": 98, "2": 99, "3": 100},
                "Italy": {"0": 101, "1": 102, "2": 103, "3": 104},
            },
            "hydroFinalLevels": {
                "France": {"0": 105, "1": 106, "2": 107, "3": 108},
                "Germany": {"0": 109, "1": 110, "2": 111, "3": 112},
                "Italy": {"0": 113, "1": 114, "2": 115, "3": 116},
            },
            "hydroGenerationPower": {
                "France": {"0": 117, "1": 118, "2": 119, "3": 120},
                "Germany": {"0": 121, "1": 122, "2": 123, "3": 124},
                "Italy": {"0": 125, "1": 126, "2": 127, "3": 128},
            },
            "shortTermStorage": {
                "France": {"0": 129, "1": 130, "2": 131, "3": 132},
                "Germany": {"0": 133, "1": 134, "2": 135, "3": 136},
                "Italy": {"0": 137, "1": 138, "2": 139, "3": 140},
            },
        }
        for scenario_type, table in table_form.items():
            ruleset.set_table_form(table, scenario_type)
        actual_rules = ruleset.get_rules()
        expected = {
            "bc,main,0": 85,
            "bc,main,1": 86,
            "bc,main,2": 87,
            "bc,main,3": 88,
            "bc,secondary,0": 89,
            "bc,secondary,1": 90,
            "bc,secondary,2": 91,
            "bc,secondary,3": 92,
            "h,france,0": 5,
            "h,france,1": 6,
            "h,france,3": 8,
            "h,germany,0": 9,
            "h,germany,1": 10,
            "h,germany,2": 11,
            "h,germany,3": 12,
            "h,italy,0": 13,
            "h,italy,2": 15,
            "h,italy,3": 16,
            "hfl,france,0": 1.05,
            "hfl,france,1": 1.06,
            "hfl,france,2": 1.07,
            "hfl,france,3": 1.08,
            "hfl,germany,0": 1.09,
            "hfl,germany,1": 1.1,
            "hfl,germany,2": 1.11,
            "hfl,germany,3": 1.12,
            "hfl,italy,0": 1.13,
            "hfl,italy,1": 1.14,
            "hfl,italy,2": 1.15,
            "hfl,italy,3": 1.16,
            "hgp,france,0": 117,
            "hgp,france,1": 118,
            "hgp,france,2": 119,
            "hgp,france,3": 120,
            "hgp,germany,0": 121,
            "hgp,germany,1": 122,
            "hgp,germany,2": 123,
            "hgp,germany,3": 124,
            "hgp,italy,0": 125,
            "hgp,italy,1": 126,
            "hgp,italy,2": 127,
            "hgp,italy,3": 128,
            "sts,france,0": 129,
            "sts,france,1": 130,
            "sts,france,2": 131,
            "sts,france,3": 132,
            "sts,germany,0": 133,
            "sts,germany,1": 134,
            "sts,germany,2": 135,
            "sts,germany,3": 136,
            "sts,italy,0": 137,
            "sts,italy,1": 138,
            "sts,italy,2": 139,
            "sts,italy,3": 140,
            "hl,france,0": 0.93,
            "hl,france,1": 0.94,
            "hl,france,2": 0.95,
            "hl,france,3": 0.96,
            "hl,germany,0": 0.97,
            "hl,germany,1": 0.98,
            "hl,germany,2": 0.99,
            "hl,germany,3": 1.0,
            "hl,italy,0": 1.01,
            "hl,italy,1": 1.02,
            "hl,italy,2": 1.03,
            "hl,italy,3": 1.04,
            "l,france,0": 1,
            "l,france,1": 2,
            "l,france,2": 3,
            "l,france,3": 4,
            "l,germany,0": 5,
            "l,germany,1": 6,
            "l,germany,2": 7,
            "l,germany,3": 8,
            "l,italy,0": 9,
            "ntc,germany,france,0": 77,
            "ntc,germany,france,1": 78,
            "ntc,germany,france,2": 79,
            "ntc,germany,france,3": 80,
            "ntc,italy,france,0": 81,
            "ntc,italy,france,1": 82,
            "ntc,italy,france,2": 83,
            "ntc,italy,france,3": 84,
            "r,france,0,wind offshore": 65,
            "r,france,0,wind onshore": 69,
            "r,france,1,wind offshore": 66,
            "r,france,1,wind onshore": 70,
            "r,france,2,wind offshore": 67,
            "r,france,2,wind onshore": 71,
            "r,france,3,wind offshore": 68,
            "r,france,3,wind onshore": 72,
            "r,germany,0,wind onshore": 73,
            "r,germany,1,wind onshore": 74,
            "r,germany,2,wind onshore": 75,
            "r,germany,3,wind onshore": 76,
            "s,france,0": 29,
            "s,france,1": 30,
            "s,france,2": 31,
            "s,france,3": 32,
            "s,germany,0": 33,
            "s,germany,1": 34,
            "s,germany,2": 35,
            "s,germany,3": 36,
            "s,italy,0": 37,
            "s,italy,1": 38,
            "s,italy,2": 39,
            "s,italy,3": 40,
            "t,france,0,coal": 45,
            "t,france,0,nuclear": 41,
            "t,france,1,coal": 46,
            "t,france,1,nuclear": 42,
            "t,france,2,coal": 47,
            "t,france,2,nuclear": 43,
            "t,france,3,coal": 48,
            "t,france,3,nuclear": 44,
            "t,germany,0,fuel": 53,
            "t,germany,0,gaz": 49,
            "t,germany,1,fuel": 54,
            "t,germany,1,gaz": 50,
            "t,germany,2,fuel": 55,
            "t,germany,2,gaz": 51,
            "t,germany,3,fuel": 56,
            "t,germany,3,gaz": 52,
            "t,italy,0,fuel": 61,
            "t,italy,0,nuclear": 57,
            "t,italy,1,fuel": 62,
            "t,italy,1,nuclear": 58,
            "t,italy,2,fuel": 63,
            "t,italy,2,nuclear": 59,
            "t,italy,3,fuel": 64,
            "t,italy,3,nuclear": 60,
            "w,france,0": 17,
            "w,france,1": 18,
            "w,france,2": 19,
            "w,france,3": 20,
            "w,germany,0": 21,
            "w,germany,1": 22,
            "w,germany,2": 23,
            "w,germany,3": 24,
            "w,italy,0": 25,
            "w,italy,1": 26,
            "w,italy,2": 27,
            "w,italy,3": 28,
        }
        assert actual_rules == expected
        # fmt: off
        assert ruleset.get_table_form("load") == table_form["load"]
        assert ruleset.get_table_form("hydro") == table_form["hydro"]
        assert ruleset.get_table_form("wind") == table_form["wind"]
        assert ruleset.get_table_form("solar") == table_form["solar"]
        assert ruleset.get_table_form("thermal") == table_form["thermal"]
        assert ruleset.get_table_form("renewable") == table_form["renewable"]
        assert ruleset.get_table_form("link") == table_form["link"]
        assert ruleset.get_table_form("bindingConstraints") == table_form["bindingConstraints"]
        assert ruleset.get_table_form("hydroInitialLevels") == table_form["hydroInitialLevels"]
        assert ruleset.get_table_form("hydroFinalLevels") == table_form["hydroFinalLevels"]
        assert ruleset.get_table_form("hydroGenerationPower") == table_form["hydroGenerationPower"]
        assert ruleset.get_table_form("shortTermStorage") == table_form["shortTermStorage"]

        # fmt: on

        with pytest.raises(KeyError):
            ruleset.get_table_form("invalid")

    @pytest.mark.parametrize(
        "table_form, expected",
        [
            ({"France": {"0": 23}}, 23),
            ({"France": {"0": None}}, np.nan),
            ({"France": {"0": ""}}, np.nan),
        ],
    )
    @pytest.mark.parametrize("old_value", [12, None, np.nan, ""], ids=["int", "None", "NaN", "empty"])
    def test_update_table_form(
        self,
        ruleset: RulesetMatrices,
        table_form: TableForm,
        expected: float,
        old_value: t.Union[int, float, str],
    ) -> None:
        ruleset.scenarios["load"].at["France", "0"] = old_value
        ruleset.update_table_form(table_form, "load")
        actual = ruleset.scenarios["load"].at["France", "0"]
        assert np.isnan(expected) and np.isnan(actual) or expected == actual
        actual_table_form = ruleset.get_table_form("load")
        assert actual_table_form["France"]["0"] == ("" if np.isnan(expected) else expected)
