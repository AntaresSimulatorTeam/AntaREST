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
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationArea
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.replace_hydro_correlation import ReplaceHydroCorrelation
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


def _set_up(study: FileStudy, command_context: CommandContext) -> FileStudyTreeDao:
    # Creates several areas with different correlations
    correlation_cfg = {
        "N?%N?": 1.0,  # Write the area name in the file to ensure we're able to read the data
        "e%e": 1.0,
        "s%n": 0.2,
        "s%w": 0.6,
        "e%w": 0.1,
    }

    dao = build_dao_from_file_study(study, command_context)
    for area_name in ["N?", "s", "e", "w"]:
        CreateArea(area_name=area_name, command_context=command_context, study_version=study.config.version).apply(dao)

    study.tree.save(correlation_cfg, ["input", "hydro", "prepro", "correlation", "annual"])
    return dao


def test_nominal_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    dao = _set_up(study, command_context)

    cmd = ReplaceHydroCorrelation(
        area_id="e",
        correlation=HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="w", coefficient=1),
                HydroCorrelationArea(area_id="n", coefficient=2.3),
            ]
        ),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(dao)
    assert output.status

    # Checks the ini content
    ini_path = study.config.study_path / "input" / "hydro" / "prepro" / "correlation.ini"
    assert (
        ini_path.read_text()
        == """[general]
mode = annual

[annual]
e%n = 0.023
e%w = 0.01
n%s = 0.2
s%w = 0.6

"""
    )


def test_error_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    dao = _set_up(study, command_context)

    # Fake area
    cmd = ReplaceHydroCorrelation(
        area_id="fake_area",
        correlation=HydroCorrelation(correlation=[HydroCorrelationArea(area_id="e", coefficient=1)]),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(dao)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message

    # Fake area inside the correlation parameter
    cmd = ReplaceHydroCorrelation(
        area_id="e",
        correlation=HydroCorrelation(correlation=[HydroCorrelationArea(area_id="fake_area", coefficient=1)]),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(dao)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message
