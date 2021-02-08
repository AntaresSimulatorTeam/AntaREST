from pathlib import Path

from antarest.storage.filesystem.config.model import Area, StudyConfig
from antarest.storage.filesystem.root.settings.scenariobuilder import (
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
        "01_solar",
        "02_wind_on",
        "03_wind_off",
        "04_res",
        "05_nuclear",
        "06_coal",
        "07_gas",
        "08_non-res",
        "09_hydro_pump",
    ]

    areas = {
        n: Area(
            links=[], thermals=thermals, filters_year=[], filters_synthesis=[]
        )
        for n in ["de", "fr", "es", "it"]
    }

    node = ScenarioBuilder(
        StudyConfig(study_path=path, areas=areas, outputs=dict())
    )

    assert node.get(["Default Ruleset", "t,it,0,09_hydro_pump"]) == 1
