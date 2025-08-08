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

import os
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.core.serde.ini_reader import read_ini
from antarest.core.serde.ini_writer import write_ini_file
from antarest.study.business.model.config.timeseries_config_model import (
    TimeSeriesConfiguration,
    TimeSeriesConfigurationUpdate,
    TimeSeriesType,
)
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.business.timeseries_config_management import (
    TimeSeriesConfigManager,
)
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.fixture
def file_study_820(tmpdir: Path) -> FileStudy:
    cur_dir: Path = Path(__file__).parent
    study_path = Path(tmpdir / str(uuid.uuid4()))
    os.mkdir(study_path)
    with ZipFile(cur_dir / "assets" / "empty_study_820.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, "1")
    return FileStudy(config, FileStudyTree(Mock(), config))


def test_nominal_case(file_study_820: FileStudy, command_context: CommandContext):
    # Checks default value
    assert file_study_820.tree.get(["settings", "generaldata", "general", "nbtimeseriesthermal"]) == 1

    study = FileStudyInterface(file_study_820)

    # Prepares the test
    config_manager = TimeSeriesConfigManager(command_context)

    # Asserts the get method returns the right value
    assert config_manager.get_timeseries_configuration(study) == TimeSeriesConfiguration(
        thermal=TimeSeriesType(number=1)
    )

    # Modifies the value and asserts the get takes the modification into account
    new_value = TimeSeriesConfigurationUpdate(thermal=TimeSeriesType(number=2))
    config_manager.set_timeseries_configuration(study, new_value)
    assert config_manager.get_timeseries_configuration(study) == TimeSeriesConfiguration(
        thermal=TimeSeriesType(number=2)
    )


def test_missing_value(file_study_820: FileStudy, command_context: CommandContext):
    ini_path = file_study_820.config.study_path / "settings" / "generaldata.ini"
    content = read_ini(ini_path)
    assert content["general"]["nbtimeseriesthermal"] == 1

    # Removes the key from the file
    del content["general"]["nbtimeseriesthermal"]
    write_ini_file(ini_path, content)

    # The reading method should still succeed and return the right value
    config_manager = TimeSeriesConfigManager(command_context)
    study = FileStudyInterface(file_study_820)

    assert config_manager.get_timeseries_configuration(study) == TimeSeriesConfiguration(
        thermal=TimeSeriesType(number=1)
    )

    # Setting a new value should modify the ini file
    new_value = TimeSeriesConfigurationUpdate(thermal=TimeSeriesType(number=2))
    config_manager.set_timeseries_configuration(study, new_value)
    content = read_ini(ini_path)
    assert content["general"]["nbtimeseriesthermal"] == 2
