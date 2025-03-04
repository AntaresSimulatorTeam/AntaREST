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
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.areas.hydro_management import FIELDS_INFO, HydroManager
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext

hydro_ini_content = {
    "input": {
        "hydro": {
            "hydro": {
                "inter-daily-breakdown": {"AreaTest1": 2, "AREATEST2": 3, "area_test_3": 4},
                "intra-daily-modulation": {"AreaTest1": 25, "AREATEST2": 26, "area_test_3": 27},
                "inter-monthly-breakdown": {"AreaTest1": 1, "AREATEST2": 1, "area_test_3": 1},
                "initialize reservoir date": {"AreaTest1": 0, "AREATEST2": 1, "area_test_3": 2},
                "pumping efficiency": {"AreaTest1": 1, "AREATEST2": 1, "area_test_3": 1},
                "use leeway": {
                    "AreaTest1": True,
                },
                "leeway low": {
                    "AreaTest1": 1,
                },
            }
        }
    }
}


@pytest.fixture(name="hydro_manager")
def hydro_manager_fixture(
    raw_study_service: RawStudyService,
    generator_matrix_constants: GeneratorMatrixConstants,
    simple_matrix_service: SimpleMatrixService,
) -> HydroManager:
    hydro_manager = HydroManager(
        command_context=CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=simple_matrix_service,
        )
    )
    return hydro_manager


@pytest.fixture(name="study")
def study_interface_fixture(tmp_path: Path) -> FileStudyInterface:
    study_id = "study_test"
    study_path = tmp_path.joinpath(f"tmp/{study_id}")
    config = build(study_path, study_id)
    tree = FileStudyTree(Mock(spec=ContextServer), config)
    tree.save(hydro_ini_content)

    file_study_interface = FileStudyInterface(file_study=FileStudy(config=config, tree=tree))

    return file_study_interface


class TestHydroManagement:
    @pytest.mark.unit_test
    def test_get_field_values(self, hydro_manager: HydroManager, study: FileStudyInterface) -> None:
        """
        Set up:
            Retrieve a study service and a study interface
            Create some areas with different letter cases
        Test:
            Check if `get_field_values` returns the right values
        """
        # add som areas
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        # gather initial data of the area
        for area in areas:
            # get actual value
            data = hydro_manager.get_field_values(study, area).model_dump()

            # set expected value based on defined fields dict
            raw_data = hydro_ini_content["input"]["hydro"]["hydro"]
            initial_data = dict.fromkeys(FIELDS_INFO.keys())

            for key in initial_data:
                initial_data[key] = FIELDS_INFO[key]["default_value"]

            for key in raw_data.keys():
                reformatted_key = key.replace("-", "_").replace(" ", "_")
                initial_data[reformatted_key] = raw_data[key].get(area, initial_data[reformatted_key])

            # check if the area is retrieved regardless of the letters case
            assert data == initial_data
