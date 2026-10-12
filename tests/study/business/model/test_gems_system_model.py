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
from antarest.study.business.model.gems.system import GemsSystem

COMPONENTS = [{"id": "electrolyser", "model": "library.electrolyser"}]

AREA_CONNECTION = {"component": "electrolyser", "port": "power_port", "area": "West-H2"}
THERMAL_CAPACITY_CONNECTION = {
    "component": "electrolyser",
    "port": "power_port",
    "thermal-component": {"area": "West", "cluster-id": "Gas_Cluster"},
}


def test_legacy_ids_are_lowercased() -> None:
    system = GemsSystem.model_validate(
        {
            "id": "sys",
            "components": COMPONENTS,
            "area-connections": [AREA_CONNECTION],
            "thermal-capacity-connections": [THERMAL_CAPACITY_CONNECTION],
        }
    )

    assert system.area_connections[0].area == "west-h2"
    assert system.thermal_capacity_connections[0].thermal_component.area == "west"
    assert system.thermal_capacity_connections[0].thermal_component.cluster_id == "gas_cluster"


def test_a_port_can_have_both_an_area_and_a_thermal_capacity_connection() -> None:
    system = GemsSystem.model_validate(
        {
            "id": "sys",
            "components": COMPONENTS,
            "area-connections": [AREA_CONNECTION],
            "thermal-capacity-connections": [THERMAL_CAPACITY_CONNECTION],
        }
    )

    assert len(system.area_connections) == 1
    assert len(system.thermal_capacity_connections) == 1
