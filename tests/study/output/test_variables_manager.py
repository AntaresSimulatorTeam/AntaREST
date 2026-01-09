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

from antarest.core.exceptions import OutputVariablesViewError
from antarest.study.output.output_model import OutputVariablesList
from antarest.study.output.variables_management import (
    AreaOutputId,
    LinkOutputId,
    OutputItemId,
    RenewableClusterOutputId,
    ShortTermStorageOutputId,
    ThermalClusterOutputId,
    check_output_variable_exists,
)

AVAILABLE_VARIABLES = OutputVariablesList(
    **{
        "mcInd": {
            "areas": [
                {
                    "name": "fr",
                    "variables": ["AVL DTG", "BALANCE", "CO2 EMIS.", "COAL"],
                    "thermalClusters": [{"name": "01_solar", "variables": ["MWh", "NODU", "NP Cost - Euro"]}],
                    "renewableClusters": [{"name": "01_renew", "variables": ["MWh", "NODU", "NP Cost - Euro"]}],
                    "shortTermStorages": [{"name": "01_sts", "variables": ["MWh", "NODU", "NP Cost - Euro"]}],
                }
            ],
            "links": [{"area1Name": "de", "area2Name": "fr", "variables": ["LOOP FLOW", "MARG. COST", "UCAP LIN."]}],
        },
        "mcAll": {"areas": [], "links": []},
    }
)


# fmt: off
@pytest.mark.parametrize(
    "variable_name, item_id, error_msg",
    [
        # Area
        pytest.param("a", AreaOutputId(area_id="fake_area"), "The variable 'a' does not exist for area 'fake_area' and type 'area'", id="Area does not exist"),
        pytest.param("fake_variable", AreaOutputId(area_id="fr"), "The variable 'fake_variable' does not exist for area 'fr' and type 'area'", id="Area variable does not exist"),
        # Thermal
        pytest.param("", ThermalClusterOutputId(area_id="fr", thermal_id="fake_th"), "The variable '' does not exist for area 'fr' and type 'thermal'", id="Thermal does not exist"),
        pytest.param("fake_var", ThermalClusterOutputId(area_id="fr", thermal_id="01_solar"), "The variable 'fake_var' does not exist for area 'fr' and type 'thermal'", id="Thermal variable does not exist"),
        # Renewable
        pytest.param("", RenewableClusterOutputId(area_id="fr", renewable_id="fake_re"), "The variable '' does not exist for area 'fr' and type 'renewable'", id="Renewable does not exist"),
        pytest.param("fake_var", RenewableClusterOutputId(area_id="fr", renewable_id="01_renew"), "The variable 'fake_var' does not exist for area 'fr' and type 'renewable'", id="Renewable variable does not exist"),
        # Short-term storage
        pytest.param("", ShortTermStorageOutputId(area_id="fr", st_storage_id="fake_sts"), "The variable '' does not exist for area 'fr' and type 'st_storage'", id="STS does not exist"),
        pytest.param("fake_var", ShortTermStorageOutputId(area_id="fr", st_storage_id="01_sts"), "The variable 'fake_var' does not exist for area 'fr' and type 'st_storage'", id="STS variable does not exist"),
        # Links
        pytest.param("", LinkOutputId(area_from_id="de", area_to_id="fr"), "The variable '' does not exist for link 'de - fr'", id="Link does not exist"),
        pytest.param("fake_var", LinkOutputId(area_from_id="de", area_to_id="fake_area"), "The variable 'fake_var' does not exist for link 'de - fake_area'", id="Link variable does not exist"),
    ],
)
#fmt: on
def test_check_variables_exists_errors(
    variable_name: str,
    item_id: OutputItemId,
    error_msg: str,
) -> None:
    with pytest.raises(OutputVariablesViewError, match=error_msg):

        check_output_variable_exists("", variable_name, AVAILABLE_VARIABLES, item_id)


@pytest.mark.parametrize(
    "variable_name, item_id",
    [
        pytest.param("AVL DTG", AreaOutputId(area_id="fr"), id="Area"),
        pytest.param("NODU", ThermalClusterOutputId(area_id="fr", thermal_id="01_solar"), id="Thermal"),
        pytest.param("MWh", RenewableClusterOutputId(area_id="fr", renewable_id="01_renew"), id="Renewable"),
        pytest.param("NP Cost - Euro", ShortTermStorageOutputId(area_id="fr", st_storage_id="01_sts"),
                     id="Short term storage"),
        pytest.param("LOOP FLOW", LinkOutputId(area_from_id="de", area_to_id="fr"), id="Link"),
    ],
)
#fmt: on
def test_check_variables_exists_success(variable_name: str, item_id: OutputItemId) -> None:
    # Ensures the method doesn't raise
    check_output_variable_exists("", variable_name, AVAILABLE_VARIABLES, item_id)
