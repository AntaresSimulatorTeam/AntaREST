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

from antarest.core.exceptions import OutputVariablesViewError
from antarest.study.business.output.variables_management import (
    AreaOutputIdentifier,
    LinkOutputIdentifier,
    OutputIdentifier,
    RenewableClusterOutputIdentifier,
    ShortTermStorageOutputIdentifier,
    ThermalClusterOutputIdentifier,
    check_arguments_coherence_and_return_identifier,
    check_output_variable_exists,
)
from antarest.study.storage.output_model import OutputVariablesList, OutputVariablesType

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
    "variable_type, variable_name, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id, error_msg",
    [
        # Area
        pytest.param(OutputVariablesType.AREA, "", None, None, None, None, None, None, "You should provide `area_id` for areas", id="Area w/o area_id"),
        pytest.param(OutputVariablesType.AREA, "", "", "area_from_id", None, None, None, None, "You provided an link related id for areas", id="Area with `area_from_id`"),
        pytest.param(OutputVariablesType.AREA, "", "", None, "area_to_id", None, None, None, "You provided an link related id for areas", id="Area with `area_to_id`"),
        # Thermal
        pytest.param(OutputVariablesType.THERMAL, "", "area", None, None, None, None, None, "You should provide `thermal_id` for thermal clusters", id="Thermal w/o `thermal_id`"),
        pytest.param(OutputVariablesType.THERMAL, "", "area", None, None, "th", "r", None, "You provided an storage/renewable id for thermal clusters", id="Thermal with `renewable_id`"),
        pytest.param(OutputVariablesType.THERMAL, "", "area", None, None, "th", None, "sts", "You provided an storage/renewable id for thermal clusters", id="Thermal with `st_storage_id`"),
        # Renewable
        pytest.param(OutputVariablesType.RENEWABLE, "", "area", None, None, None, None, None, "You should provide `renewable_id` for renewable clusters", id="Renewable w/o `renewable_id`"),
        pytest.param(OutputVariablesType.RENEWABLE, "", "area", None, None, "th", "r", None, "You provided an storage/thermal id for renewable clusters", id="Renewable with `thermal_id`"),
        pytest.param(OutputVariablesType.RENEWABLE, "", "area", None, None, None, "r", "sts", "You provided an storage/thermal id for renewable clusters", id="Renewable with `st_storage_id`"),
        # Short-term storage
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "", "area", None, None, None, None, None, "You should provide `st_storage_id` for short-term storages", id="STS w/o `st_storage_id`"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "", "area", None, None, None, "th", "sts", "You provided an renewable/thermal id for short-term storages", id="STS with `thermal_id`"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "", "area", None, None, "r", None, "sts", "You provided an renewable/thermal id for short-term storages", id="STS with `st_storage_id`"),
        # Links
        pytest.param(OutputVariablesType.LINK, None, None, "", None, None, None, None, "You should provide both `area_from_id` and `area_to_id` for links", id="Link w/o area_from_id"),
        pytest.param(OutputVariablesType.LINK, None, None, None, "", None, None, None, "You should provide both `area_from_id` and `area_to_id` for links", id="Link w/o area_to_id"),
        pytest.param(OutputVariablesType.LINK, None, "area", "a", "b", None, None, None, "You provided an area related id for links", id="Link with area_id"),
        pytest.param(OutputVariablesType.LINK, None, None, "a", "b", "th", None, None, "You provided an area related id for links", id="Link with thermal_id"),
        pytest.param(OutputVariablesType.LINK, None, None, "a", "b", None, "renew", None, "You provided an area related id for links", id="Link with renewable_id"),
        pytest.param(OutputVariablesType.LINK, None, None, "a", "b", None, None, "sts", "You provided an area related id for links", id="Link with st_storage_id"),
    ],
)
#fmt: on
def test_check_variables_view_coherence_errors(
    variable_type: OutputVariablesType,
    variable_name: str,
    area_id: str | None,
    area_from_id: str | None,
    area_to_id: str | None,
    thermal_id: str | None,
    renewable_id: str | None,
    st_storage_id: str | None,
    error_msg: str,
) -> None:
    with pytest.raises(OutputVariablesViewError, match=error_msg):
        check_arguments_coherence_and_return_identifier(variable_type, "", area_id, area_from_id, area_to_id,
                                                        thermal_id, renewable_id, st_storage_id)


# fmt: off
@pytest.mark.parametrize(
    "variable_type, variable_name, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id, error_msg",
    [
        # Area
        pytest.param(OutputVariablesType.AREA, "a", "fake_area", None, None, None, None, None, "The variable 'a' does not exist for area 'fake_area' and type 'area'", id="Area does not exist"),
        pytest.param(OutputVariablesType.AREA, "fake_variable", "fr", None, None, None, None, None, "The variable 'fake_variable' does not exist for area 'fr' and type 'area'", id="Area variable does not exist"),
        # Thermal
        pytest.param(OutputVariablesType.THERMAL, "", "fr", None, None, "fake_th", None, None, "The variable '' does not exist for area 'fr' and type 'thermal'", id="Thermal does not exist"),
        pytest.param(OutputVariablesType.THERMAL, "fake_var", "fr", None, None, "01_solar", None, None, "The variable 'fake_var' does not exist for area 'fr' and type 'thermal'", id="Thermal variable does not exist"),
        # Renewable
        pytest.param(OutputVariablesType.RENEWABLE, "", "fr", None, None, None, "fake_re", None, "The variable '' does not exist for area 'fr' and type 'renewable'", id="Renewable does not exist"),
        pytest.param(OutputVariablesType.RENEWABLE, "fake_var", "fr", None, None, None, "01_renew", None, "The variable 'fake_var' does not exist for area 'fr' and type 'renewable'", id="Renewable variable does not exist"),
        # Short-term storage
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "", "fr", None, None, None, None, "fake_sts", "The variable '' does not exist for area 'fr' and type 'st_storage'", id="STS does not exist"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "fake_var", "fr", None, None, None, None, "01_sts", "The variable 'fake_var' does not exist for area 'fr' and type 'st_storage'", id="STS variable does not exist"),
        # Links
        pytest.param(OutputVariablesType.LINK, "", None, "de", "fr", None, None, None, "The variable '' does not exist for link 'de - fr'", id="Link does not exist"),
        pytest.param(OutputVariablesType.LINK, "fake_var", None, "de", "fake_area", None, None, None, "The variable 'fake_var' does not exist for link 'de - fake_area'", id="Link variable does not exist"),
    ],
)
#fmt: on
def test_check_variables_exists_errors(
    variable_type: OutputVariablesType,
    variable_name: str,
    area_id: str | None,
    area_from_id: str | None,
    area_to_id: str | None,
    thermal_id: str | None,
    renewable_id: str | None,
    st_storage_id: str | None,
    error_msg: str,
) -> None:
    output_identifier = check_arguments_coherence_and_return_identifier(variable_type, "", area_id, area_from_id,
                                                                        area_to_id,
                                                                        thermal_id, renewable_id, st_storage_id)

    with pytest.raises(OutputVariablesViewError, match=error_msg):

        check_output_variable_exists("", variable_type, variable_name, AVAILABLE_VARIABLES, output_identifier)


# fmt: off
@pytest.mark.parametrize(
    "variable_type, variable_name, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id, expected_result",
    [
        pytest.param(OutputVariablesType.AREA, "AVL DTG", "fr", None, None, None, None, None, AreaOutputIdentifier(area_id="fr"), id="Area"),
        pytest.param(OutputVariablesType.THERMAL, "NODU", "fr", None, None, "01_solar", None, None, ThermalClusterOutputIdentifier(area_id="fr", cluster_id="01_solar"), id="Thermal"),
        pytest.param(OutputVariablesType.RENEWABLE, "MWh", "fr", None, None, None, "01_renew", None, RenewableClusterOutputIdentifier(area_id="fr", cluster_id="01_renew"), id="Renewable"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "NP Cost - Euro", "fr", None, None, None, None, "01_sts", ShortTermStorageOutputIdentifier(area_id="fr", storage_id="01_sts"), id="Short term storage"),
        pytest.param(OutputVariablesType.LINK, "LOOP FLOW", None, "de", "fr", None, None, None, LinkOutputIdentifier(area_from_id="de", area_to_id="fr"), id="Link"),
    ],
)
#fmt: on
def test_get_variables_view_coherence_success(
    variable_type: OutputVariablesType,
    variable_name: str,
    area_id: str | None,
    area_from_id: str | None,
    area_to_id: str | None,
    thermal_id: str | None,
    renewable_id: str | None,
    st_storage_id: str | None,
expected_result: OutputIdentifier
) -> None:
    output_identifier = check_arguments_coherence_and_return_identifier(variable_type, "", area_id, area_from_id,
                                                                        area_to_id, thermal_id, renewable_id,
                                                                        st_storage_id)
    assert expected_result == output_identifier

    # Ensures the method doesn't crash
    check_output_variable_exists("", variable_type, variable_name, AVAILABLE_VARIABLES, output_identifier)
