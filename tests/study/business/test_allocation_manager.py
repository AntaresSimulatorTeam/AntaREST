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

import numpy as np
import pytest

from antarest.study.business.allocation_management import AllocationManager
from antarest.study.business.model.hydro_allocation_model import (
    HydroAllocation,
    HydroAllocationArea,
    HydroAllocationMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface


def _set_up(command_context: CommandContext, study: FileStudy) -> None:
    allocation_cfg = {
        "n": {"[allocation]": {"N?": 1}},  # Write the area name in the file to ensure we're able to read the data
        "e": {"allocation": {"e": 3, "s": 1}},
        "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
        "w": {"[allocation]": {"w": 1}},
    }

    for area_name in ["N?", "s", "e", "w"]:
        CreateArea(area_name=area_name, command_context=command_context, study_version=study.config.version).apply(
            study
        )

        area_id = transform_name_to_id(area_name)
        study.tree.save(allocation_cfg[area_id], ["input", "hydro", "allocation", area_id])


@pytest.fixture
def manager(command_context: CommandContext) -> AllocationManager:
    return AllocationManager(command_context)


def test_error_cases() -> None:
    # Check that the allocation is not empty
    with pytest.raises(ValueError, match="empty"):
        HydroAllocation(allocation=[])

    # Check that the allocation does not contain duplicate area IDs
    with pytest.raises(ValueError, match="duplicate"):
        HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="north", coefficient=0.75),
                HydroAllocationArea(area_id="north", coefficient=0.25),
            ],
        )

    # Check that negative coefficients are accepted
    fields = HydroAllocation(
        allocation=[
            HydroAllocationArea(area_id="NORTH", coefficient=-0.75),
            HydroAllocationArea(area_id="SOUTH", coefficient=1.25),
        ]
    )
    assert fields.allocation[0].coefficient == -0.75
    assert fields.allocation[1].coefficient == 1.25

    # Check that at least one coefficient should be non-zero
    with pytest.raises(ValueError, match="non-zero"):
        HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="NORTH", coefficient=0),
                HydroAllocationArea(area_id="SOUTH", coefficient=0),
            ],
        )

    # Check that the coefficients sum is positive
    with pytest.raises(ValueError, match="positive"):
        HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="NORTH", coefficient=-0.75),
                HydroAllocationArea(area_id="SOUTH", coefficient=-0.25),
            ],
        )

    # Check that the coefficients do not contain NaN coefficients
    with pytest.raises(ValueError, match="Input should be a finite number"):
        HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="NORTH", coefficient=0.75),
                HydroAllocationArea(area_id="SOUTH", coefficient=float("nan")),
            ],
        )

    # Check that the matrix is not empty
    with pytest.raises(ValueError, match="empty"):
        HydroAllocationMatrix.from_hydro_allocations({})


def test_get_allocation_matrix(
    manager: AllocationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    study = file_study_interface(empty_study_920)
    matrix = manager.get_allocation_matrix(study)

    # Check
    assert matrix.index == matrix.columns == ["e", "n", "s", "w"]
    assert np.array_equal(
        matrix.data,
        np.array(
            [
                [3.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.2, 0.1, 0.6],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )


def test_get_allocation_for_area(
    manager: AllocationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    expected_allocations = {
        "e": HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="e", coefficient=3.0),
                HydroAllocationArea(area_id="s", coefficient=1.0),
            ]
        ),
        "n": HydroAllocation(allocation=[HydroAllocationArea(area_id="n", coefficient=1.0)]),
        "s": HydroAllocation(
            allocation=[
                HydroAllocationArea(area_id="s", coefficient=0.1),
                HydroAllocationArea(area_id="n", coefficient=0.2),
                HydroAllocationArea(area_id="w", coefficient=0.6),
            ]
        ),
        "w": HydroAllocation(allocation=[HydroAllocationArea(area_id="w", coefficient=1.0)]),
    }

    study = file_study_interface(empty_study_920)
    for area_id in expected_allocations:
        allocation = manager.get_allocation_for_area(study, area_id)
        assert allocation == expected_allocations[area_id]


def test_set_allocation_for_area(
    manager: AllocationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    study = file_study_interface(empty_study_920)

    new_allocation = HydroAllocation(
        allocation=[
            HydroAllocationArea(area_id="s", coefficient=3.0),
            HydroAllocationArea(area_id="n", coefficient=12.1),
        ]
    )
    alloc = manager.set_allocation_for_area(study, "e", new_allocation)
    assert alloc == new_allocation
    assert manager.get_allocation_for_area(study, "e") == new_allocation
