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

from typing import Any
from unittest.mock import Mock

import pytest

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.study.dao.utils import save_area


@pytest.fixture
def filestudy_dao_v10_2(empty_study_930: FileStudy, matrix_service: ISimpleMatrixService) -> FileStudyTreeDao:
    empty_study_930.config.version = STUDY_VERSION_10_2
    constants = GeneratorMatrixConstants(matrix_service)
    constants.init_constant_matrices()
    return FileStudyTreeDao(
        empty_study_930,
        False,
        constants,
        InMemoryBlobService(),
        matrix_service,
        Mock(),
    )


def _make_reserve(name: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
    base = dict(
        name=name,
        type=reserve_type,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )
    base.update(overrides)
    return ReserveDefinition(**base)


def test_yaml_file_is_written_and_read_correctly(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    save_area(filestudy_dao_v10_2, "paris")
    global_params = ReservesGlobalParameters(
        reference_activation_duration_down=5,
        energy_activation_ratio_down=0.33,
        reference_activation_duration_up=11,
        energy_activation_ratio_up=0.66,
    )
    filestudy_dao_v10_2.save_reserves_global_parameters({"paris": global_params})

    # Check the YML content
    study_path = (
        filestudy_dao_v10_2.get_file_study().config.study_path / "input" / "reserves" / "paris" / "reserves.yml"
    )
    content = YAMLReader().read(study_path)
    expected_content: dict[str, Any] = {
        "globalparameters": {
            "energy-activation-ratio-down": 0.33,
            "energy-activation-ratio-up": 0.66,
            "reference-activation-duration-down": 5,
            "reference-activation-duration-up": 11,
        }
    }
    assert content == expected_content

    # Add a reserve definition
    filestudy_dao_v10_2.save_reserve_definitions({"paris": [_make_reserve("R1", failure_cost=999)]})

    # Check the YML content
    content = YAMLReader().read(study_path)
    expected_content["reserves"] = [
        {
            "energy-activation-ratio": 0.9,
            "failure-cost": 999.0,
            "name": "R1",
            "power-activation-ratio": 0.4,
            "reference-activation-duration": 3,
            "spillage-cost": 5.0,
            "type": "up",
        }
    ]
    assert content == expected_content
