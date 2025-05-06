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

from pathlib import Path

from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.settings.scenariobuilder import ScenarioBuilder

RULES = {
    "h,de,0": 1,
    "h,es,0": 1,
    "h,fr,0": 1,
    "h,it,0": 1,
    "l,de,0": 1,
    "l,es,0": 1,
    "l,fr,0": 1,
    "l,it,0": 1,
    "s,de,0": 1,
    "s,es,0": 1,
    "s,fr,0": 1,
    "s,it,0": 1,
    "ntc,de,fr,0": 34,
    "ntc,de,fr,1": 45,
    "ntc,de,it,0": 56,
    "ntc,de,it,1": 67,
    "t,de,0,01_solar": 11,
    "t,de,0,02_wind_on": 12,
    "t,de,0,03_wind_off": 13,
    "t,de,0,04_res": 14,
    "t,de,0,05_nuclear": 15,
    "t,de,0,06_coal": 16,
    "t,de,0,07_gas": 17,
    "t,de,0,08_non-res": 18,
    "t,de,0,09_hydro_pump": 19,
    "t,es,0,01_solar": 21,
    "t,es,0,02_wind_on": 22,
    "t,es,0,03_wind_off": 23,
    "t,es,0,04_res": 24,
    "t,es,0,05_nuclear": 25,
    "t,es,0,06_coal": 26,
    "t,es,0,07_gas": 27,
    "t,es,0,08_non-res": 28,
    "t,es,0,09_hydro_pump": 29,
    "t,fr,0,01_solar": 31,
    "t,fr,1,01_solar": 31,
    "t,fr,0,02_wind_on": 32,
    "t,fr,1,02_wind_on": 32,
    "t,fr,0,03_wind_off": 33,
    "t,fr,1,03_wind_off": 33,
    "t,fr,0,04_res": 34,
    "t,fr,1,04_res": 34,
    "t,fr,0,05_nuclear": 35,
    "t,fr,1,05_nuclear": 35,
    "t,fr,0,06_coal": 36,
    "t,fr,1,06_coal": 36,
    "t,fr,0,07_gas": 37,
    "t,fr,1,07_gas": 37,
    "t,fr,0,08_non-res": 38,
    "t,fr,1,08_non-res": 38,
    "t,fr,0,09_hydro_pump": 39,
    "t,it,0,01_solar": 41,
    "t,it,0,02_wind_on": 42,
    "t,it,0,03_wind_off": 43,
    "t,it,0,04_res": 44,
    "t,it,0,05_nuclear": 45,
    "t,it,0,06_coal": 46,
    "t,it,0,07_gas": 47,
    "t,it,0,08_non-res": 48,
    "t,it,0,09_hydro_pump": 49,
    "w,de,0": 1,
    "w,es,0": 1,
    "w,fr,0": 1,
    "w,it,0": 1,
    # since v8.7
    "bc,group a,0": 1,
    "bc,group a,1": 2,
    "bc,group b,0": 2,
    "bc,group b,1": 1,
}


def test_get(tmp_path: Path) -> None:
    path = tmp_path / "file.ini"
    with open(path, mode="w") as f:
        print("[Default Ruleset]", file=f)
        for key, value in RULES.items():
            print(f"{key} = {value}", file=f)

    thermals = [
        ThermalCluster(name="01_solar", enabled=True),
        ThermalCluster(name="02_wind_on", enabled=True),
        ThermalCluster(name="03_wind_off", enabled=True),
        ThermalCluster(name="04_res", enabled=True),
        ThermalCluster(name="05_nuclear", enabled=True),
        ThermalCluster(name="06_coal", enabled=True),
        ThermalCluster(name="07_gas", enabled=True),
        ThermalCluster(name="08_non-res", enabled=True),
        ThermalCluster(name="09_hydro_pump", enabled=True),
    ]

    areas = {
        n: Area(
            name=n,
            links=dict(),
            thermals=thermals,
            renewables=[],
            filters_year=[],
            filters_synthesis=[],
        )
        for n in ["de", "fr", "es", "it"]
    }

    node = ScenarioBuilder(
        config=FileStudyTreeConfig(
            study_path=path,
            path=path,
            version=870,
            areas=areas,
            outputs=dict(),
            study_id="id",
        ),
    )

    actual = node.get()
    assert actual == {"Default Ruleset": RULES}

    actual = node.get(["Default Ruleset"])
    assert actual == RULES

    assert node.get(["Default Ruleset", "t,it,0,09_hydro_pump"]) == 49

    # since v8.7
    assert node.get(["Default Ruleset", "bc,group a,0"]) == 1
    assert node.get(["Default Ruleset", "bc,group a,1"]) == 2
    assert node.get(["Default Ruleset", "bc,group b,0"]) == 2
    assert node.get(["Default Ruleset", "bc,group b,1"]) == 1

    actual = node.get(["Default Ruleset", "w,de,0"])
    assert actual == 1

    # We can also filter the data by generator type
    actual = node.get(["Default Ruleset", "s"])
    assert actual == {"s,de,0": 1, "s,es,0": 1, "s,fr,0": 1, "s,it,0": 1}

    # We can filter the data by generator type and area (or group for BC)
    actual = node.get(["Default Ruleset", "t", "fr"])
    expected = {
        "t,fr,0,01_solar": 31,
        "t,fr,0,02_wind_on": 32,
        "t,fr,0,03_wind_off": 33,
        "t,fr,0,04_res": 34,
        "t,fr,0,05_nuclear": 35,
        "t,fr,0,06_coal": 36,
        "t,fr,0,07_gas": 37,
        "t,fr,0,08_non-res": 38,
        "t,fr,0,09_hydro_pump": 39,
        "t,fr,1,01_solar": 31,
        "t,fr,1,02_wind_on": 32,
        "t,fr,1,03_wind_off": 33,
        "t,fr,1,04_res": 34,
        "t,fr,1,05_nuclear": 35,
        "t,fr,1,06_coal": 36,
        "t,fr,1,07_gas": 37,
        "t,fr,1,08_non-res": 38,
    }
    assert actual == expected

    # We can filter the data by generator type, area and cluster
    actual = node.get(["Default Ruleset", "t", "fr", "01_solar"])
    assert actual == {"t,fr,0,01_solar": 31, "t,fr,1,01_solar": 31}

    # We can filter the data by link type
    actual = node.get(["Default Ruleset", "ntc", "de", "fr"])
    assert actual == {"ntc,de,fr,0": 34, "ntc,de,fr,1": 45}
