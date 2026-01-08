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
import re

import numpy as np
import pytest

from antarest.study.business.correlation_management import CorrelationManager
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationArea,
    HydroCorrelationMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface


def _set_up(command_context: CommandContext, study: FileStudy) -> None:
    correlation_cfg = {
        "N?%N?": 1.0,  # Write the area name in the file to ensure we're able to read the data
        "e%e": 1.0,
        "s%n": 0.2,
        "s%w": 0.6,
        "e%w": 0.1,
    }

    for area_name in ["N?", "s", "e", "w"]:
        CreateArea(area_name=area_name, command_context=command_context, study_version=study.config.version).apply(
            study
        )

    study.tree.save(correlation_cfg, ["input", "hydro", "prepro", "correlation", "annual"])


@pytest.fixture
def manager(command_context: CommandContext) -> CorrelationManager:
    return CorrelationManager(command_context)


def test_error_cases() -> None:
    # correlation must not be empty
    with pytest.raises(ValueError, match="must not be empty"):
        HydroCorrelation(correlation=[])

    # correlation must not contain duplicate area IDs
    with pytest.raises(ValueError, match="duplicate area IDs"):
        HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="NORTH", coefficient=50),
                HydroCorrelationArea(area_id="NORTH", coefficient=25),
                HydroCorrelationArea(area_id="SOUTH", coefficient=25),
            ]
        )

    # coefficients must be between -100 and 100 and not be NaN
    for coefficient in [-101, 101, np.nan]:
        with pytest.raises(ValueError, match="Input should be"):
            HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="NORTH", coefficient=coefficient),
                ]
            )

        with pytest.raises(ValueError, match="correlation matrix must not contain"):
            HydroCorrelationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=np.array([[np.nan, np.nan], [np.nan, np.nan]]),
            )

    # matrix cannot be empty
    with pytest.raises(ValueError, match="must not be empty"):
        HydroCorrelationMatrix(index=[], columns=[], data=np.array([]))

    # Matrix index and columns should be the same
    with pytest.raises(ValueError, match="correlation matrix must have the same rows and columns"):
        HydroCorrelationMatrix(
            index=["fr", "de"],
            columns=["fr"],
            data=np.array([[1, 2], [3, 4]]),
        )

    # Matrix array shape should match the index and columns
    with pytest.raises(ValueError, match=re.escape("correlation matrix must have shape (2×2)")):
        HydroCorrelationMatrix(
            index=["fr", "de"],
            columns=["fr", "de"],
            data=np.array([[0.1], [0.3]]),
        )

    # The matrix should be symmetric
    with pytest.raises(ValueError, match="not symmetric"):
        HydroCorrelationMatrix(
            index=["fr", "de"],
            columns=["fr", "de"],
            data=np.array([[0.1, 0.2], [0.3, 0.4]]),
        )

    # The matrix diagonal should only contain "1"
    with pytest.raises(ValueError, match="correlation diagonal should be filled with 1"):
        HydroCorrelationMatrix(
            index=["fr", "de"],
            columns=["fr", "de"],
            data=np.array([[0.1, 0.0], [0.0, 1.0]]),
        )


def test_get_correlation_matrix(
    manager: CorrelationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    study = file_study_interface(empty_study_920)
    matrix = manager.get_correlation_matrix(study)

    # Check
    assert matrix.index == matrix.columns == ["e", "n", "s", "w"]
    assert np.array_equal(
        matrix.data,
        np.array(
            [
                [1.0, 0.0, 0.0, 0.1],
                [0.0, 1.0, 0.2, 0.0],
                [0.0, 0.2, 1.0, 0.6],
                [0.1, 0.0, 0.6, 1.0],
            ]
        ),
    )


def test_get_correlation_for_area(
    manager: CorrelationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    expected_correlations = {
        "e": HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="e", coefficient=100.0),
                HydroCorrelationArea(area_id="n", coefficient=0.0),
                HydroCorrelationArea(area_id="s", coefficient=0.0),
                HydroCorrelationArea(area_id="w", coefficient=10.0),
            ]
        ),
        "n": HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="e", coefficient=0.0),
                HydroCorrelationArea(area_id="n", coefficient=100.0),
                HydroCorrelationArea(area_id="s", coefficient=20.0),
                HydroCorrelationArea(area_id="w", coefficient=0.0),
            ],
        ),
        "s": HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="e", coefficient=0.0),
                HydroCorrelationArea(area_id="n", coefficient=20.0),
                HydroCorrelationArea(area_id="s", coefficient=100.0),
                HydroCorrelationArea(area_id="w", coefficient=60.0),
            ]
        ),
        "w": HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="e", coefficient=10.0),
                HydroCorrelationArea(area_id="n", coefficient=0.0),
                HydroCorrelationArea(area_id="s", coefficient=60.0),
                HydroCorrelationArea(area_id="w", coefficient=100.0),
            ]
        ),
    }

    study = file_study_interface(empty_study_920)
    for area_id in expected_correlations:
        correlation = manager.get_correlation_for_area(study, area_id)
        assert correlation == expected_correlations[area_id]


def test_set_correlation_for_area(
    manager: CorrelationManager, empty_study_920: FileStudy, command_context: CommandContext
) -> None:
    _set_up(command_context, empty_study_920)

    study = file_study_interface(empty_study_920)

    new_correlation = HydroCorrelation(
        correlation=[
            HydroCorrelationArea(area_id="s", coefficient=3.0),
            HydroCorrelationArea(area_id="n", coefficient=12.1),
        ]
    )
    corr = manager.set_correlation_for_area(study, "e", new_correlation)
    assert corr == new_correlation
    assert manager.get_correlation_for_area(study, "e") == HydroCorrelation(
        correlation=[
            HydroCorrelationArea(area_id="e", coefficient=100.0),
            HydroCorrelationArea(area_id="n", coefficient=12.1),
            HydroCorrelationArea(area_id="s", coefficient=3.0),
            HydroCorrelationArea(area_id="w", coefficient=0.0),  # Should be reset to 0 as it wasn't modified
        ]
    )
