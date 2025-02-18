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

from unittest.mock import Mock

import numpy as np
import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.area_management import AreaInfoDTO, AreaType
from antarest.study.business.correlation_management import (
    AreaCoefficientItem,
    CorrelationFormFields,
    CorrelationManager,
    CorrelationMatrix,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.fixture
def correlation_manager(command_context: CommandContext) -> CorrelationManager:
    return CorrelationManager(command_context)


class TestCorrelationField:
    def test_init__nominal_case(self):
        field = AreaCoefficientItem(area_id="NORTH", coefficient=100)
        assert field.area_id == "NORTH"
        assert field.coefficient == 100

    def test_init__camel_case_args(self):
        field = AreaCoefficientItem(areaId="NORTH", coefficient=100)
        assert field.area_id == "NORTH"
        assert field.coefficient == 100


class TestCorrelationFormFields:
    def test_init__nominal_case(self):
        fields = CorrelationFormFields(
            correlation=[
                {"area_id": "NORTH", "coefficient": 75},
                {"area_id": "SOUTH", "coefficient": 25},
            ]
        )
        assert fields.correlation == [
            AreaCoefficientItem(area_id="NORTH", coefficient=75),
            AreaCoefficientItem(area_id="SOUTH", coefficient=25),
        ]

    def test_validation__coefficients_not_empty(self):
        """correlation must not be empty"""
        with pytest.raises(ValueError, match="must not be empty"):
            CorrelationFormFields(correlation=[])

    def test_validation__coefficients_no_duplicates(self):
        """correlation must not contain duplicate area IDs:"""
        with pytest.raises(ValueError, match="duplicate area IDs") as ctx:
            CorrelationFormFields(
                correlation=[
                    {"area_id": "NORTH", "coefficient": 50},
                    {"area_id": "NORTH", "coefficient": 25},
                    {"area_id": "SOUTH", "coefficient": 25},
                ]
            )
        assert "NORTH" in str(ctx.value)  # duplicates

    @pytest.mark.parametrize("coefficient", [-101, 101, np.nan])
    def test_validation__coefficients_invalid_values(self, coefficient):
        """coefficients must be between -100 and 100"""
        with pytest.raises(ValueError, match="between -100 and 100|must not contain NaN"):
            CorrelationFormFields(
                correlation=[
                    {"area_id": "NORTH", "coefficient": coefficient},
                ]
            )


class TestCorrelationMatrix:
    def test_init__nominal_case(self):
        field = CorrelationMatrix(
            index=["fr", "de"],
            columns=["fr"],
            data=[
                [1.0],
                [0.2],
            ],
        )
        assert field.index == ["fr", "de"]
        assert field.columns == ["fr"]
        assert field.data == [
            [1.0],
            [0.2],
        ]

    def test_validation__coefficients_non_empty_array(self):
        """Check that the coefficients matrix is a non-empty array"""

        with pytest.raises(ValueError, match="must not be empty"):
            CorrelationMatrix(
                index=[],
                columns=[],
                data=[],
            )

    def test_validation__coefficients_array_shape(self):
        """Check that the coefficients matrix is an array of shape 2×1"""
        with pytest.raises(ValueError, match=r"must have shape \(\d+×\d+\)"):
            CorrelationMatrix(
                index=["fr", "de"],
                columns=["fr"],
                data=[[1, 2], [3, 4]],
            )

    @pytest.mark.parametrize("coefficient", [-1.1, 1.1, np.nan])
    def test_validation__coefficients_invalid_value(self, coefficient):
        """Check that all coefficients matrix has positive or nul coefficients"""

        with pytest.raises(ValueError, match="between -1 and 1|must not contain NaN"):
            CorrelationMatrix(
                index=["fr", "de"],
                columns=["fr", "de"],
                data=[
                    [1.0, coefficient],
                    [0.2, 0],
                ],
            )

    def test_validation__matrix_not_symmetric(self):
        """Check that the correlation matrix is not symmetric"""
        with pytest.raises(ValueError, match=r"not symmetric"):
            CorrelationMatrix(
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
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        # run
        matrix = correlation_manager.get_correlation_matrix(all_areas=all_areas, study=study, columns=[])

        # Check
        assert matrix == CorrelationMatrix(
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
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        fields = correlation_manager.get_correlation_form_fields(all_areas=all_areas, study=study, area_id=area_id)
        assert fields == CorrelationFormFields(
            correlation=[
                AreaCoefficientItem(area_id="s", coefficient=100.0),
                AreaCoefficientItem(area_id="n", coefficient=20.0),
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
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "s"  # South
        correlation_manager.set_correlation_form_fields(
            all_areas=all_areas,
            study=study,
            area_id=area_id,
            data=CorrelationFormFields(
                correlation=[
                    AreaCoefficientItem(area_id="s", coefficient=100),
                    AreaCoefficientItem(area_id="e", coefficient=30),
                    AreaCoefficientItem(area_id="n", coefficient=40),
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
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n"  # South

        with pytest.raises(AreaNotFound) as ctx:
            correlation_manager.set_correlation_form_fields(
                all_areas=all_areas,
                study=study,
                area_id=area_id,
                data=CorrelationFormFields(
                    correlation=[
                        AreaCoefficientItem(area_id="UNKNOWN", coefficient=3.14),
                    ]
                ),
            )
        assert "'UNKNOWN'" in ctx.value.detail
        study.add_commands.assert_not_called()
