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

from antarest.output.output_blueprint import _to_item_id
from antarest.output.output_model import OutputVariablesType
from antarest.output.variables_management import (
    AreaOutputId,
    LinkOutputId,
    OutputItemId,
    RenewableClusterOutputId,
    ShortTermStorageOutputId,
    ThermalClusterOutputId,
)


# fmt: off
@pytest.mark.parametrize(
    "variable_type, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id",
    [
        # Area
        pytest.param(OutputVariablesType.AREA, None, None, None, None, None, None, id="Area w/o area_id"),
        pytest.param(OutputVariablesType.AREA, "", "area_from_id", None, None, None, None, id="Area with `area_from_id`"),
        pytest.param(OutputVariablesType.AREA, "", None, "area_to_id", None, None, None, id="Area with `area_to_id`"),
        # Thermal
        pytest.param(OutputVariablesType.THERMAL, "area", None, None, None, None, None, id="Thermal w/o `thermal_id`"),
        pytest.param(OutputVariablesType.THERMAL, "area", None, None, "th", "r", None, id="Thermal with `renewable_id`"),
        pytest.param(OutputVariablesType.THERMAL, "area", None, None, "th", None, "sts", id="Thermal with `st_storage_id`"),
        # Renewable
        pytest.param(OutputVariablesType.RENEWABLE, "area", None, None, None, None, None, id="Renewable w/o `renewable_id`"),
        pytest.param(OutputVariablesType.RENEWABLE, "area", None, None, "th", "r", None, id="Renewable with `thermal_id`"),
        pytest.param(OutputVariablesType.RENEWABLE, "area", None, None, None, "r", "sts", id="Renewable with `st_storage_id`"),
        # Short-term storage
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "area", None, None, None, None, None, id="STS w/o `st_storage_id`"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "area", None, None, None, "th", "sts", id="STS with `thermal_id`"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "area", None, None, "r", None, "sts", id="STS with `st_storage_id`"),
        # Links
        pytest.param(OutputVariablesType.LINK, None, "", None, None, None, None, id="Link w/o area_from_id"),
        pytest.param(OutputVariablesType.LINK, None, None, "", None, None, None, id="Link w/o area_to_id"),
        pytest.param(OutputVariablesType.LINK, "area", "a", "b", None, None, None, id="Link with area_id"),
        pytest.param(OutputVariablesType.LINK, None, "a", "b", "th", None, None, id="Link with thermal_id"),
        pytest.param(OutputVariablesType.LINK, None, "a", "b", None, "renew", None, id="Link with renewable_id"),
        pytest.param(OutputVariablesType.LINK, None, "a", "b", None, None, "sts", id="Link with st_storage_id"),
    ],
)
#fmt: on
def test_output_item_id_coherence_errors(
    variable_type: OutputVariablesType,
    area_id: str | None,
    area_from_id: str | None,
    area_to_id: str | None,
    thermal_id: str | None,
    renewable_id: str | None,
    st_storage_id: str | None,
) -> None:
    with pytest.raises(ValueError):
        _to_item_id(variable_type, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id)


# fmt: off
@pytest.mark.parametrize(
    "variable_type, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id, expected_result",
    [
        pytest.param(OutputVariablesType.AREA, "fr", None, None, None, None, None, AreaOutputId(area_id="fr"),
                     id="Area"),
        pytest.param(OutputVariablesType.THERMAL, "fr", None, None, "01_solar", None, None,
                     ThermalClusterOutputId(area_id="fr", thermal_id="01_solar"), id="Thermal"),
        pytest.param(OutputVariablesType.RENEWABLE, "fr", None, None, None, "01_renew", None,
                     RenewableClusterOutputId(area_id="fr", renewable_id="01_renew"), id="Renewable"),
        pytest.param(OutputVariablesType.SHORT_TERM_STORAGE, "fr", None, None, None, None,
                     "01_sts", ShortTermStorageOutputId(area_id="fr", st_storage_id="01_sts"), id="Short term storage"),
        pytest.param(OutputVariablesType.LINK, None, "de", "fr", None, None, None,
                     LinkOutputId(area_from_id="de", area_to_id="fr"), id="Link"),
    ],
)
#fmt: on
def test_output_item_id_coherence_success(
    variable_type: OutputVariablesType,
    area_id: str | None,
    area_from_id: str | None,
    area_to_id: str | None,
    thermal_id: str | None,
    renewable_id: str | None,
    st_storage_id: str | None,
    expected_result: OutputItemId
) -> None:
    output_identifier = _to_item_id(variable_type, area_id, area_from_id,
                                                                        area_to_id, thermal_id, renewable_id,
                                                                        st_storage_id)
    assert expected_result == output_identifier
