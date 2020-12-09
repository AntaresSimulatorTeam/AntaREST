from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.root.study import Study
from tests.filesystem.utils import extract_sta


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("input/areas/de/ui/ui/x", 1),
        (
            "input/areas/de/optimization/filtering/filter-synthesis",
            "daily, monthly",
        ),
        ("input/areas/list", "file/STA-mini/input/areas/list.txt"),
        ("input/bindingconstraints/bindingconstraints", {}),
        ("input/hydro/allocation/fr/[allocation/fr", 1),
        (
            "input/hydro/common/capacity/reservoir_es",
            "file/STA-mini/input/hydro/common/capacity/reservoir_es.txt",
        ),
        (
            "input/hydro/prepro/it/energy",
            "file/STA-mini/input/hydro/prepro/it/energy.txt",
        ),
        ("input/hydro/prepro/it/prepro/prepro/intermonthly-correlation", 0.5),
        ("input/hydro/prepro/correlation/general/mode", "annual"),
        (
            "input/hydro/series/es/ror",
            "file/STA-mini/input/hydro/series/es/ror.txt",
        ),
        (
            "input/hydro/series/es/mod",
            "file/STA-mini/input/hydro/series/es/mod.txt",
        ),
        ("input/hydro/hydro/leeway low/de", 1.0),
        ("input/links/de/fr", "file/STA-mini/input/links/de/fr.txt"),
        ("input/links/de/properties/fr/loop-flow", False),
        ("input/load/prepro/it/k", "file/STA-mini/input/load/prepro/it/k.txt"),
        (
            "input/load/prepro/it/data",
            "file/STA-mini/input/load/prepro/it/data.txt",
        ),
        (
            "input/load/prepro/it/conversion",
            "file/STA-mini/input/load/prepro/it/conversion.txt",
        ),
        (
            "input/load/prepro/it/translation",
            "file/STA-mini/input/load/prepro/it/translation.txt",
        ),
        ("input/load/prepro/correlation/general/mode", "annual"),
        (
            "input/load/series/load_fr",
            "file/STA-mini/input/load/series/load_fr.txt",
        ),
        (
            "input/misc-gen/miscgen-it",
            "file/STA-mini/input/misc-gen/miscgen-it.txt",
        ),
        ("input/reserves/es", "file/STA-mini/input/reserves/es.txt"),
        (
            "input/solar/prepro/de/k",
            "file/STA-mini/input/solar/prepro/de/k.txt",
        ),
        (
            "input/solar/series/solar_de",
            "file/STA-mini/input/solar/series/solar_de.txt",
        ),
        (
            "input/wind/prepro/de/k",
            "file/STA-mini/input/wind/prepro/de/k.txt",
        ),
        (
            "input/wind/series/wind_de",
            "file/STA-mini/input/wind/series/wind_de.txt",
        ),
        ("input/thermal/clusters/de/list/01_solar/unitcount", 1),
        ("input/thermal/areas/unserverdenergycost/es", 3000),
        (
            "input/thermal/prepro/es/06_coal/data",
            "file/STA-mini/input/thermal/prepro/es/06_coal/data.txt",
        ),
        (
            "input/thermal/prepro/es/06_coal/modulation",
            "file/STA-mini/input/thermal/prepro/es/06_coal/modulation.txt",
        ),
        (
            "input/thermal/series/it/07_gas/series",
            "file/STA-mini/input/thermal/series/it/07_gas/series.txt",
        ),
    ],
)
def test_get_input_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
) -> None:
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config.from_path(path))

    assert study.get(url.split("/")) == exp


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("input/areas/de/ui/ui/x", 42),
        (
            "input/areas/de/optimization/filtering/filter-synthesis",
            "Hello, World",
        ),
        (
            "input/bindingconstraints/bindingconstraints",
            {"Hello": {"World": 42}},
        ),
        ("input/hydro/allocation/fr/[allocation/fr", 42),
        ("input/hydro/prepro/it/prepro/prepro/intermonthly-correlation", 42.0),
        ("input/hydro/prepro/correlation/general/mode", "Hello World"),
        ("input/hydro/hydro/leeway low/de", 42),
        ("input/links/de/properties/fr/loop-flow", True),
        ("input/load/prepro/correlation/general/mode", "Hello World"),
        ("input/thermal/clusters/de/list/01_solar/unitcount", 42),
        ("input/thermal/areas/unserverdenergycost/es", 42.0),
    ],
)
def test_save_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
) -> None:
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config.from_path(path))

    study.save(exp, url.split("/"))
    assert study.get(url.split("/")) == exp
