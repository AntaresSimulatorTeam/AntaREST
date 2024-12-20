# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import pathlib
import zipfile
from typing import Sequence

import pytest

from antarest.core.config import Config

HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")


# All ZIP files have the same file tree structure because empty studies are similar.
# There are only real differences when the user sets up the study or runs simulations
# (e.g. the outputs are different).
STUDY_FILES = [
    "Desktop.ini",
    "input/",
    "input/areas/",
    "input/areas/list.txt",
    "input/areas/sets.ini",
    "input/bindingconstraints/",
    "input/bindingconstraints/bindingconstraints.ini",
    "input/hydro/",
    "input/hydro/allocation/",
    "input/hydro/common/",
    "input/hydro/common/capacity/",
    "input/hydro/hydro.ini",
    "input/hydro/prepro/",
    "input/hydro/prepro/correlation.ini",
    "input/hydro/series/",
    "input/links/",
    "input/load/",
    "input/load/prepro/",
    "input/load/prepro/correlation.ini",
    "input/load/series/",
    "input/misc-gen/",
    "input/reserves/",
    "input/solar/",
    "input/solar/prepro/",
    "input/solar/prepro/correlation.ini",
    "input/solar/series/",
    "input/thermal/",
    "input/thermal/areas.ini",
    "input/thermal/clusters/",
    "input/thermal/prepro/",
    "input/thermal/series/",
    "input/wind/",
    "input/wind/prepro/",
    "input/wind/prepro/correlation.ini",
    "input/wind/series/",
    "layers/",
    "layers/layers.ini",
    "logs/",
    "output/",
    "settings/",
    "settings/comments.txt",
    "settings/generaldata.ini",
    "settings/resources/",
    "settings/resources/study.ico",
    "settings/scenariobuilder.dat",
    "settings/simulations/",
    "study.antares",
    "user/",
]


@pytest.mark.parametrize(
    "filename, expected_list",
    [
        ("empty_study_850.zip", STUDY_FILES),
        ("empty_study_840.zip", STUDY_FILES),
        ("empty_study_830.zip", STUDY_FILES),
        ("empty_study_820.zip", STUDY_FILES),
        ("empty_study_810.zip", STUDY_FILES),
        ("empty_study_803.zip", STUDY_FILES),
        ("empty_study_720.zip", STUDY_FILES),
        ("empty_study_710.zip", STUDY_FILES),
        ("empty_study_700.zip", STUDY_FILES),
        ("empty_study_613.zip", STUDY_FILES),
    ],
)
def test_empty_study_zip(filename: str, expected_list: Sequence[str]):
    resource_path = RESOURCES_DIR.joinpath(filename)
    with zipfile.ZipFile(resource_path) as myzip:
        actual = sorted(myzip.namelist())
    assert actual == expected_list


def test_resources_config():
    """
    Check that the "resources/config.yaml" file is valid.

    The launcher section must be configured to use a local launcher
    with NB Cores detection enabled.
    """
    config_path = RESOURCES_DIR.joinpath("deploy/config.yaml")
    config = Config.from_yaml_file(config_path, res=RESOURCES_DIR)
    assert config.launcher.default == "local"
    assert config.launcher.local is not None
    assert config.launcher.local.enable_nb_cores_detection is True
