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
from antarest.study.business.areas.hydro_management import HydroManager
from antarest.study.business.model.hydro_management_model import HydroManagementOptions
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
    def test_get_hydro_management_options(self, hydro_manager: HydroManager, study: FileStudyInterface) -> None:
        """
        Set up:
            Retrieve a study service and a study interface
            Create some areas with different letter cases
        Test:
            Check if `get_hydro_management_options` returns the right values
        """
        # add som areas
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        # gather initial data of the area
        for area in areas:
            # get actual value
            data_area_raw = hydro_manager.get_hydro_management_options(study, area).model_dump()

            # get values if area_id is in lower case
            data_area_lower = hydro_manager.get_hydro_management_options(study, area.lower()).model_dump()

            # get values if area_id is in upper case
            data_area_upper = hydro_manager.get_hydro_management_options(study, area.upper()).model_dump()

            # check if the area is retrieved regardless of the letters case
            assert data_area_raw == data_area_lower
            assert data_area_raw == data_area_upper

    @pytest.mark.unit_test
    def test_set_field_values(self, tmp_path: Path, hydro_manager: HydroManager, study: FileStudyInterface) -> None:
        """
        Set up:
            Retrieve a study service and a study interface
            Create some areas with different letter cases
            Simulate changes by an external tool
        Test:
            Get data with changes on character cases
            Simulate a regular change
            Check if the field was successfully edited for each area without duplicates
        """
        # store the area ids
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        for area in areas:
            # get initial values with get_hydro_management_options
            initial_data = hydro_manager.get_hydro_management_options(study, area).model_dump()

            # simulate changes on area_id case with another tool
            hydro_ini_path = tmp_path.joinpath(f"tmp/{study.id}/input/hydro/hydro.ini")
            with open(hydro_ini_path) as f:
                file_content = f.read()
                file_content = file_content.replace(area, area.lower())

            with open(hydro_ini_path, "w") as f:
                f.write(file_content)

            # make sure that `get_hydro_management_options` retrieve same data as before
            new_data = hydro_manager.get_hydro_management_options(study, area).model_dump()
            assert initial_data == new_data

            # simulate regular usage by modifying some values
            modified_data = dict(initial_data)
            modified_data["intra_daily_modulation"] = 5.0
            hydro_manager.update_hydro_management_options(study, HydroManagementOptions(**modified_data), area)

            # retrieve edited
            new_data = hydro_manager.get_hydro_management_options(study, area).model_dump()

            # check if the intra daily modulation was modified
            for field, value in new_data.items():
                if field == "intra_daily_modulation":
                    assert initial_data[field] != new_data[field]
                else:
                    assert initial_data[field] == new_data[field]
