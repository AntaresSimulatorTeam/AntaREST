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
from pathlib import Path

import pytest

from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.variables_parsing import parse_output_variables


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


def test_extract_area_variables(output_dir: Path) -> None:
    output = FileOutput(output_dir)
    parsing_result = parse_output_variables(output)

    # Notes: weird stuff in input data: CO2 emissions in MWh, and different naming for thermal production groups
    assert parsing_result.mc_ind_areas.variables == [
        VariableDescription(name="CO2 EMIS.", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type=None),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type=None),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type=None),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type=None),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type=None),
    ]
    assert parsing_result.mc_ind_areas.area_vars == {
        "@ all areas": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "es": [9, 10, 1, 2, 3, 4, 6, 5],  # we correctly get ES_NUCLEAR as 10
        "fr": [9, 11, 1, 2, 3, 4, 6, 5],  # we correctly get FR_NUCLEAR as 11
    }

    assert parsing_result.mc_all_areas.variables == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="EXP"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="std"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="min"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="max"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="std"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="min"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="max"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="std"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="min"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="max"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="std"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="min"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="max"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="EXP"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="std"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="min"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="max"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="std"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="min"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="max"),
        VariableDescription(name="NODU", unit=None, statistic_type="EXP"),
        VariableDescription(name="NODU", unit=None, statistic_type="std"),
        VariableDescription(name="NODU", unit=None, statistic_type="min"),
        VariableDescription(name="NODU", unit=None, statistic_type="max"),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type="std"),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type="min"),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type="max"),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type="std"),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type="min"),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type="max"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="std"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="min"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="max"),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type="std"),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type="min"),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type="max"),
    ]
    assert parsing_result.mc_all_areas.area_vars == {
        "@ all areas": [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
        ],
        "es": [
            0,
            1,
            2,
            3,
            36,
            37,
            38,
            39,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            24,
            25,
            26,
            27,
            20,
            21,
            22,
            23,
        ],
        "fr": [
            0,
            1,
            2,
            3,
            40,
            41,
            42,
            43,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            24,
            25,
            26,
            27,
            20,
            21,
            22,
            23,
        ],
    }
