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

import pathlib

import pytest
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp

from antarest.core.config import Config

HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")


# All ZIP files have the same file tree structure because empty studies are similar.
# There are only real differences when the user sets up the study or runs simulations
# (e.g. the outputs are different).
STUDY_FILES = [
    "Desktop.ini",
    "input",
    "input/areas",
    "input/areas/list.txt",
    "input/areas/sets.ini",
    "input/bindingconstraints",
    "input/bindingconstraints/bindingconstraints.ini",
    "input/hydro",
    "input/hydro/allocation",
    "input/hydro/common",
    "input/hydro/common/capacity",
    "input/hydro/hydro.ini",
    "input/hydro/prepro",
    "input/hydro/prepro/correlation.ini",
    "input/hydro/series",
    "input/links",
    "input/load",
    "input/load/prepro",
    "input/load/prepro/correlation.ini",
    "input/load/series",
    "input/misc-gen",
    "input/reserves",
    "input/solar",
    "input/solar/prepro",
    "input/solar/prepro/correlation.ini",
    "input/solar/series",
    "input/thermal",
    "input/thermal/areas.ini",
    "input/thermal/clusters",
    "input/thermal/prepro",
    "input/thermal/series",
    "input/wind",
    "input/wind/prepro",
    "input/wind/prepro/correlation.ini",
    "input/wind/series",
    "layers",
    "layers/layers.ini",
    "logs",
    "output",
    "settings",
    "settings/comments.txt",
    "settings/generaldata.ini",
    "settings/resources",
    "settings/resources/study.ico",
    "settings/scenariobuilder.dat",
    "settings/simulations",
    "study.antares",
    "user",
]

FILES_SINCE_V86 = sorted(["input/st-storage", "input/st-storage/clusters", "input/st-storage/series"] + STUDY_FILES)


@pytest.mark.parametrize(
    "version", ["700", "710", "720", "800", "810", "820", "830", "840", "850", "860", "870", "880"]
)
def test_empty_study_zip(tmp_path: pathlib.Path, version: StudyVersion):
    study_path = tmp_path / "test"
    app = CreateApp(study_dir=study_path, caption="Test", version=version, author="Unknown")
    app()

    existing_paths = sorted(study_path.rglob("*"))
    existing_files = []
    for file in existing_paths:
        existing_files.append(file.relative_to(study_path).as_posix())

    if StudyVersion.parse(version) < 860:
        expected_files = STUDY_FILES
    else:
        expected_files = FILES_SINCE_V86
    assert existing_files == expected_files


def test_resources_config():
    """
    Check that the "resources/config.yaml" file is valid.

    The launcher section must be configured to use a local launcher
    with NB Cores detection enabled.
    """
    config_path = RESOURCES_DIR.joinpath("deploy/config.yaml")
    config = Config.from_yaml_file(config_path, res=RESOURCES_DIR)
    assert config.launcher.default == "local_id"
    config = config.launcher.get_launcher("local_id")
    assert config is not None
    assert config.enable_nb_cores_detection is True
