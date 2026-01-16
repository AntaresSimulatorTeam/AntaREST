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
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.replace_hydro_allocation import ReplaceHydroAllocation
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(study: FileStudy, command_context: CommandContext) -> None:
    # Creates several areas with different allocations
    allocation_cfg = {
        "n": {"[allocation]": {"N?": 1}},  # Write the area name in the file to ensure we're able to read the data
        "e": {"allocation": {"e": 3, "s": 1}},  # Write the section with missing `[` to ensure we're able to read it
        "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
        "w": {"[allocation]": {"w": 1}},
    }

    for area_name in ["N?", "s", "e", "w"]:
        CreateArea(area_name=area_name, command_context=command_context, study_version=study.config.version).apply(
            study
        )

        area_id = transform_name_to_id(area_name)
        study.tree.save(allocation_cfg[area_id], ["input", "hydro", "allocation", area_id])


def test_nominal_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    _set_up(study, command_context)

    cmd = ReplaceHydroAllocation(
        area_id="e",
        allocation=HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="w", coefficient=1),
                HydroAllocationArea(area_id="n", coefficient=2.3),
            ]
        ),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert output.status

    # Checks the ini content
    ini_path = study.config.study_path / "input" / "hydro" / "allocation" / "e.ini"
    assert (
        ini_path.read_text()
        == """[[allocation]]
w = 1.0
n = 2.3

"""
    )


def test_error_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    _set_up(study, command_context)

    # Fake area
    cmd = ReplaceHydroAllocation(
        area_id="fake_area",
        allocation=HydroAllocation(allocation=[HydroAllocationArea(area_id="e", coefficient=1)]),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message

    # Fake area inside the allocation parameter
    cmd = ReplaceHydroAllocation(
        area_id="e",
        allocation=HydroAllocation(allocation=[HydroAllocationArea(area_id="fake_area", coefficient=1)]),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert not output.status
    assert "Area is not found: 'fake_area'" in output.message
