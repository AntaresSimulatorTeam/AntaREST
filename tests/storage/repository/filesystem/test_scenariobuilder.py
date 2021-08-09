from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
    Cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.scenariobuilder import (
    ScenarioBuilder,
)

content = """
[Default Ruleset]
l,de,0 = 1
l,es,0 = 1
l,fr,0 = 1
l,it,0 = 1
s,de,0 = 1
s,es,0 = 1
s,fr,0 = 1
s,it,0 = 1
h,de,0 = 1
h,es,0 = 1
h,fr,0 = 1
h,it,0 = 1
w,de,0 = 1
w,es,0 = 1
w,fr,0 = 1
w,it,0 = 1
t,de,0,01_solar = 1
t,de,0,02_wind_on = 1
t,de,0,03_wind_off = 1
t,de,0,04_res = 1
t,de,0,05_nuclear = 1
t,de,0,06_coal = 1
t,de,0,07_gas = 1
t,de,0,08_non-res = 1
t,de,0,09_hydro_pump = 1
t,es,0,01_solar = 1
t,es,0,02_wind_on = 1
t,es,0,03_wind_off = 1
t,es,0,04_res = 1
t,es,0,05_nuclear = 1
t,es,0,06_coal = 1
t,es,0,07_gas = 1
t,es,0,08_non-res = 1
t,es,0,09_hydro_pump = 1
t,fr,0,01_solar = 1
t,fr,0,02_wind_on = 1
t,fr,0,03_wind_off = 1
t,fr,0,04_res = 1
t,fr,0,05_nuclear = 1
t,fr,0,06_coal = 1
t,fr,0,07_gas = 1
t,fr,0,08_non-res = 1
t,fr,0,09_hydro_pump = 1
t,it,0,01_solar = 1
t,it,0,02_wind_on = 1
t,it,0,03_wind_off = 1
t,it,0,04_res = 1
t,it,0,05_nuclear = 1
t,it,0,06_coal = 1
t,it,0,07_gas = 1
t,it,0,08_non-res = 1
t,it,0,09_hydro_pump = 1
"""


def test_get(tmp_path: Path):
    path = tmp_path / "file.ini"
    path.write_text(content)

    thermals = [
        Cluster(id="01_solar", enabled=True),
        Cluster(id="02_wind_on", enabled=True),
        Cluster(id="03_wind_off", enabled=True),
        Cluster(id="04_res", enabled=True),
        Cluster(id="05_nuclear", enabled=True),
        Cluster(id="06_coal", enabled=True),
        Cluster(id="07_gas", enabled=True),
        Cluster(id="08_non-res", enabled=True),
        Cluster(id="09_hydro_pump", enabled=True),
    ]

    areas = {
        n: Area(
            links=dict(),
            thermals=thermals,
            renewables=[],
            filters_year=[],
            filters_synthesis=[],
        )
        for n in ["de", "fr", "es", "it"]
    }

    node = ScenarioBuilder(
        context=Mock(),
        config=FileStudyTreeConfig(
            study_path=path,
            version=-1,
            areas=areas,
            outputs=dict(),
            study_id="id",
        ),
    )

    assert node.get(["Default Ruleset", "t,it,0,09_hydro_pump"]) == 1
