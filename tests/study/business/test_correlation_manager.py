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
import re
from unittest.mock import Mock

import numpy as np
import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.correlation_management import CorrelationManager
from antarest.study.business.model.area_model import Area
from antarest.study.business.model.hydro_correlation_model import (
    HydroCorrelation,
    HydroCorrelationArea,
    HydroCorrelationMatrix,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(command_context: CommandContext, study: FileStudy) -> None:
    correlation_cfg = {
        "N?%N?": 0.1,  # Write the area name in the file to ensure we're able to read the data
        "e%e": 0.3,
        "s%s": 0.1,
        "s%n": 0.2,
        "s%w": 0.6,
        "w%w": 0.1,
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

    # matrix cannot be empty
    with pytest.raises(ValueError, match="must not be empty"):
        HydroCorrelationMatrix(index=[], columns=[], data=[])

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


class TestCorrelationMatrix:
    def test_validation__matrix_not_symmetric(self):
        """Check that the correlation matrix is not symmetric"""
        with pytest.raises(ValueError, match=r"not symmetric"):
            HydroCorrelationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[[0.1, 0.2], [0.3, 0.4]],
            )


def create_study_interface(tree: FileStudyTree, version: StudyVersion = STUDY_VERSION_8_6) -> StudyInterface:
    """
    Creates a mock study interface which returns the provided study tree.
    """
    file_study = Mock(spec=FileStudy)
    file_study.tree = tree
    study = Mock(StudyInterface)
    study.get_files.return_value = file_study
    study.version = version
    file_study.config.version = version
    return study


class TestCorrelationManager:
    def test_get_correlation_matrix__nominal_case(self, correlation_manager):
        # Prepare the mocks
        correlation_cfg = {
            "n%n": 0.1,
            "e%e": 0.3,
            "s%s": 0.1,
            "s%n": 0.2,
            "s%w": 0.6,
            "w%w": 0.1,
        }

        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=correlation_cfg),
            )
        )

        # Given the following arguments
        all_areas = [
            Area(id="n", name="North"),
            Area(id="e", name="East"),
            Area(id="s", name="South"),
            Area(id="w", name="West"),
        ]

        # run
        matrix = correlation_manager.get_correlation_matrix(all_areas=all_areas, study=study, columns=[])

        # Check
        assert matrix == HydroCorrelationMatrix(
            index=["n", "e", "s", "w"],
            columns=["n", "e", "s", "w"],
            data=[
                [1.0, 0.0, 0.2, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.2, 0.0, 1.0, 0.6],
                [0.0, 0.0, 0.6, 1.0],
            ],
        )

    def test_get_field_values__nominal_case(self, correlation_manager):
        # Prepare the mocks
        # NOTE: "s%s" value is ignored
        correlation_cfg = {"s%s": 0.1, "n%s": 0.2, "w%n": 0.6}

        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=correlation_cfg),
            )
        )

        # Given the following arguments
        all_areas = [
            Area(id="n", name="North"),
            Area(id="e", name="East"),
            Area(id="s", name="South"),
            Area(id="w", name="West"),
        ]
        area_id = "s"  # South
        fields = correlation_manager.get_correlation_for_area(all_areas=all_areas, study=study, area_id=area_id)
        assert fields == HydroCorrelation(
            correlation=[
                HydroCorrelationArea(area_id="s", coefficient=100.0),
                HydroCorrelationArea(area_id="n", coefficient=20.0),
            ]
        )

    def test_set_field_values__nominal_case(self, correlation_manager):
        # Prepare the mocks: North + South
        correlation_cfg = {}
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=correlation_cfg),
            ),
            version=STUDY_VERSION_8_8,
        )

        # Given the following arguments
        all_areas = [
            Area(id="n", name="North"),
            Area(id="e", name="East"),
            Area(id="s", name="South"),
            Area(id="w", name="West"),
        ]
        area_id = "s"  # South
        correlation_manager.set_correlation_form_fields(
            all_areas=all_areas,
            study=study,
            area_id=area_id,
            data=HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="s", coefficient=100),
                    HydroCorrelationArea(area_id="e", coefficient=30),
                    HydroCorrelationArea(area_id="n", coefficient=40),
                ]
            ),
        )

        # check update
        assert study.add_commands.call_count == 1
        mock_call = study.add_commands.mock_calls[0]
        # signature: add_commands(commands)
        (actual_cmds,) = mock_call.args
        assert len(actual_cmds) == 1
        cmd: UpdateConfig = actual_cmds[0]
        assert cmd.command_name == CommandName.UPDATE_CONFIG
        assert cmd.target == "input/hydro/prepro/correlation/annual"
        assert cmd.data == {"e%s": 0.3, "n%s": 0.4}

    def test_set_field_values__area_not_found(self, correlation_manager):
        # Prepare the mocks: North + South
        correlation_cfg = {}
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=correlation_cfg),
            ),
        )

        # Given the following arguments
        all_areas = [
            Area(id="n", name="North"),
            Area(id="e", name="East"),
            Area(id="s", name="South"),
            Area(id="w", name="West"),
        ]
        area_id = "n"  # South

        with pytest.raises(AreaNotFound) as ctx:
            correlation_manager.set_correlation_form_fields(
                all_areas=all_areas,
                study=study,
                area_id=area_id,
                data=HydroCorrelation(
                    correlation=[
                        HydroCorrelationArea(area_id="UNKNOWN", coefficient=3.14),
                    ]
                ),
            )
        assert "'UNKNOWN'" in ctx.value.detail
        study.add_commands.assert_not_called()
