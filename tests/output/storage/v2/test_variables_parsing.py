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


def test_extract_parsing_to_db(output_dir: Path) -> None:
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

    assert parsing_result.mc_all_areas.variables == []
    assert parsing_result.mc_all_areas.area_vars == {}
