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
from unittest.mock import Mock, patch

import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import AllocationDataNotFound, AreaNotFound
from antarest.study.business.allocation_management import (
    AllocationField,
    AllocationFormFields,
    AllocationManager,
    AllocationMatrix,
)
from antarest.study.business.area_management import AreaInfoDTO, AreaType
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


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


@pytest.fixture
def manager(command_context: CommandContext) -> AllocationManager:
    return AllocationManager(command_context)


class TestAllocationField:
    def test_base(self):
        field = AllocationField(areaId="NORTH", coefficient=1)
        assert field.area_id == "NORTH"
        assert field.coefficient == 1

    def test_camel_case(self):
        field = AllocationField(areaId="NORTH", coefficient=1)
        assert field.model_dump(by_alias=True) == {
            "areaId": "NORTH",
            "coefficient": 1,
        }


class TestAllocationFormFields:
    def test_base_case(self):
        fields = AllocationFormFields(
            allocation=[
                {"areaId": "NORTH", "coefficient": 0.75},
                {"areaId": "SOUTH", "coefficient": 0.25},
            ]
        )
        assert fields.allocation == [
            AllocationField(areaId="NORTH", coefficient=0.75),
            AllocationField(areaId="SOUTH", coefficient=0.25),
        ]

    def test_fields_not_empty(self):
        """Check that the coefficients column is not empty"""
        with pytest.raises(ValueError, match="empty"):
            AllocationFormFields(
                allocation=[],
            )

    def test_validation_fields_no_duplicate_area_id(self):
        """Check that the coefficients column does not contain duplicate area IDs"""
        with pytest.raises(ValueError, match="duplicate"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "NORTH", "coefficient": 0.25},
                ],
            )

    def test_validation_fields_no_negative_coefficient(self):
        """Check that the coefficients column does not contain negative coefficients"""
        with pytest.raises(ValueError, match="negative"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "SOUTH", "coefficient": -0.25},
                ],
            )

    def test_validation_fields_no_negative_sum_coefficient(self):
        """Check that the coefficients values does not sum to negative"""
        with pytest.raises(ValueError, match="negative"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": -0.75},
                    {"areaId": "SOUTH", "coefficient": -0.25},
                ],
            )

    def test_validation_fields_no_nan_coefficient(self):
        """Check that the coefficients values does not contain NaN coefficients"""
        with pytest.raises(ValueError, match="NaN"):
            AllocationFormFields(
                allocation=[
                    {"areaId": "NORTH", "coefficient": 0.75},
                    {"areaId": "SOUTH", "coefficient": float("nan")},
                ],
            )


class TestAllocationMatrix:
    def test_base_case(self):
        field = AllocationMatrix(
            index=["NORTH", "SOUTH"],
            columns=["NORTH", "SOUTH"],
            data=[[0.75, 0.25], [0.25, 0.75]],
        )
        assert field.index == ["NORTH", "SOUTH"]
        assert field.columns == ["NORTH", "SOUTH"]
        assert field.data == [[0.75, 0.25], [0.25, 0.75]]

    def test_validation_coefficients_not_empty(self):
        """Check that the coefficients matrix is not empty"""
        with pytest.raises(ValueError, match="empty"):
            AllocationMatrix(
                index=[],
                columns=[],
                data=[],
            )

    def test_validation_matrix_shape(self):
        """Check that the coefficients matrix is square"""
        with pytest.raises(ValueError, match="square"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH"],
                data=[[0.75, 0.25], [0.25, 0.75]],
            )

    def test_validation_matrix_sum_positive(self):
        """Check that the coefficients matrix sum to positive"""
        with pytest.raises(ValueError, match="negative"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0.75, -0.25], [-0.25, 0.75]],
            )

    def test_validation_matrix_no_nan(self):
        """Check that the coefficients matrix does not contain NaN values"""
        with pytest.raises(ValueError, match="NaN"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0.75, 0.25], [0.25, float("nan")]],
            )

    def test_validation_matrix_no_non_null_values(self):
        """Check that the coefficients matrix does not contain only null values"""
        with pytest.raises(ValueError, match="(?:all|zero)"):
            AllocationMatrix(
                index=["NORTH", "SOUTH"],
                columns=["NORTH", "SOUTH"],
                data=[[0, 0], [0, 0]],
            )


class TestAllocationManager:
    def test_get_allocation_matrix__nominal_case(self, manager):
        # Prepare the mocks
        allocation_cfg = {
            "n": {"[allocation]": {"n": 1}},
            "e": {"[allocation]": {"e": 3, "s": 1}},
            "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
            "w": {"[allocation]": {"w": 1}},
        }

        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=allocation_cfg),
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
        matrix = manager.get_allocation_matrix(study, all_areas)

        # Check
        assert matrix == AllocationMatrix(
            index=["n", "e", "s", "w"],
            columns=["n", "e", "s", "w"],
            data=[
                [1.0, 0.0, 0.2, 0.0],
                [0.0, 3.0, 0.0, 0.0],
                [0.0, 1.0, 0.1, 0.0],
                [0.0, 0.0, 0.6, 1.0],
            ],
        )

    def test_get_allocation_matrix__no_allocation(self, manager):
        # Prepare the mocks
        allocation_cfg = {}
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=allocation_cfg),
            )
        )

        # Given the following arguments
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        with pytest.raises(AllocationDataNotFound) as ctx:
            manager.get_allocation_matrix(study, all_areas)
        assert re.fullmatch(r"Allocation data.*is not found", ctx.value.detail)

    def test_get_allocation_form_fields__nominal_case(self, manager):
        allocation_cfg = {
            "n": {"[allocation]": {"n": 1}},
            "e": {"[allocation]": {"e": 3, "s": 1}},
            "s": {"[allocation]": {"s": 0.1, "n": 0.2, "w": 0.6}},
            "w": {"[allocation]": {"w": 1}},
        }
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=allocation_cfg["n"]),
            )
        )

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"

        fields = manager.get_allocation_form_fields(all_areas=all_areas, study=study, area_id=area_id)

        expected_allocation = [
            AllocationField.model_construct(area_id=area, coefficient=value)
            for area, value in allocation_cfg[area_id]["[allocation]"].items()
        ]
        assert fields.allocation == expected_allocation

    def test_get_allocation_form_fields__no_allocation_data(self, manager):
        allocation_cfg = {"n": {}}
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=allocation_cfg["n"]),
            )
        )

        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
        ]

        area_id = "n"

        with pytest.raises(AllocationDataNotFound) as ctx:
            manager.get_allocation_form_fields(all_areas=all_areas, study=study, area_id=area_id)
        assert "n" in ctx.value.detail

    def test_set_allocation_form_fields__nominal_case(self, manager):
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]
        area_id = "n"
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
            ),
            version=STUDY_VERSION_8_8,
        )
        with patch(
            "antarest.study.business.allocation_management.AllocationManager.get_allocation_data",
            return_value={"e": 0.5, "s": 0.25, "w": 0.25},
        ):
            manager.set_allocation_form_fields(
                all_areas=all_areas,
                study=study,
                area_id=area_id,
                data=AllocationFormFields.construct(
                    allocation=[
                        AllocationField.construct(area_id="e", coefficient=0.5),
                        AllocationField.construct(area_id="s", coefficient=0.25),
                        AllocationField.construct(area_id="w", coefficient=0.25),
                    ],
                ),
            )

        assert study.add_commands.call_count == 1
        mock_call = study.add_commands.mock_calls[0]
        (actual_commands,) = mock_call.args
        assert len(actual_commands) == 1
        cmd: UpdateConfig = actual_commands[0]
        assert cmd.command_name == CommandName.UPDATE_CONFIG
        assert cmd.target == f"input/hydro/allocation/{area_id}/[allocation]"
        assert cmd.data == {"e": 0.5, "s": 0.25, "w": 0.25}

    def test_set_allocation_form_fields__no_allocation_data(self, manager):
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
            ),
            version=STUDY_VERSION_8_8,
        )
        with patch(
            "antarest.study.business.allocation_management.AllocationManager.get_allocation_data",
            side_effect=AllocationDataNotFound(area_id),
        ):
            with pytest.raises(AllocationDataNotFound) as ctx:
                manager.set_allocation_form_fields(
                    all_areas=all_areas,
                    study=study,
                    area_id=area_id,
                    data=AllocationFormFields.model_construct(
                        allocation=[
                            AllocationField.model_construct(area_id="e", coefficient=0.5),
                            AllocationField.model_construct(area_id="s", coefficient=0.25),
                            AllocationField.model_construct(area_id="w", coefficient=0.25),
                        ],
                    ),
                )
        assert "n" in ctx.value.detail

    def test_set_allocation_form_fields__invalid_area_ids(self, manager):
        all_areas = [
            AreaInfoDTO(id="n", name="North", type=AreaType.AREA),
            AreaInfoDTO(id="e", name="East", type=AreaType.AREA),
            AreaInfoDTO(id="s", name="South", type=AreaType.AREA),
            AreaInfoDTO(id="w", name="West", type=AreaType.AREA),
        ]

        area_id = "n"
        data = AllocationFormFields.model_construct(
            allocation=[
                AllocationField.model_construct(area_id="e", coefficient=0.5),
                AllocationField.model_construct(area_id="s", coefficient=0.25),
                AllocationField.model_construct(area_id="invalid_area", coefficient=0.25),
            ]
        )

        with pytest.raises(AreaNotFound) as ctx:
            manager.set_allocation_form_fields(all_areas=all_areas, study=Mock(), area_id=area_id, data=data)

        assert "invalid_area" in ctx.value.detail
