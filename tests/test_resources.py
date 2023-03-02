import pathlib
import zipfile
from typing import Sequence

import pytest

# fmt: off
HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")
# fmt: on

STUDY_850_FILES = [
    "Desktop.ini",
    "input/",
    "input/areas/",
    "input/areas/list.txt",
    "input/areas/sets.ini",
    "input/bindingconstraints/",
    "input/bindingconstraints/bindingconstraints.ini",
    "input/hydro/",
    "input/hydro/hydro.ini",
    "input/hydro/prepro/",
    "input/hydro/prepro/correlation.ini",
    "input/load/",
    "input/load/prepro/",
    "input/load/prepro/correlation.ini",
    "input/solar/",
    "input/solar/prepro/",
    "input/solar/prepro/correlation.ini",
    "input/thermal/",
    "input/thermal/areas.ini",
    "input/wind/",
    "input/wind/prepro/",
    "input/wind/prepro/correlation.ini",
    "layers/",
    "layers/layers.ini",
    "logs/",
    "output/",
    "output/maps/",
    "settings/",
    "settings/comments.txt",
    "settings/generaldata.ini",
    "settings/resources/",
    "settings/resources/study.ico",
    "settings/scenariobuilder.dat",
    "study.antares",
    "user/",
]


@pytest.mark.parametrize(
    "filename, expected_list",
    [
        ("empty_study_850.zip", STUDY_850_FILES),
    ],
)
def test_empty_study_zip(filename: str, expected_list: Sequence[str]):
    resource_path = RESOURCES_DIR.joinpath(filename)
    with zipfile.ZipFile(resource_path) as myzip:
        actual = sorted(myzip.namelist())
    assert actual == expected_list
