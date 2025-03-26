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

import pytest

from antarest.study.business.areas.hydro_management import HydroManager
from antarest.study.business.model.hydro_model import HydroManagementUpdate
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class TestHydroManagement:
    @pytest.mark.unit_test
    def test_get_hydro_management_options(self, hydro_manager: HydroManager, empty_study_880: FileStudy) -> None:
        """
        Set up:
            Retrieve a study service and a study interface
            Create some areas with different letter cases
        Test:
            Check if `get_hydro_management_options` returns the right values
        """
        study = FileStudyInterface(empty_study_880)
        # add som areas
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        # gather initial data of the area
        for area in areas:
            # get actual value
            data_area_raw = hydro_manager.get_hydro_management(study, area).model_dump()

            # get values if area_id is in lower case
            data_area_lower = hydro_manager.get_hydro_management(study, area.lower()).model_dump()

            # get values if area_id is in upper case
            data_area_upper = hydro_manager.get_hydro_management(study, area.upper()).model_dump()

            # check if the area is retrieved regardless of the letters case
            assert data_area_raw == data_area_lower
            assert data_area_raw == data_area_upper

    @pytest.mark.unit_test
    def test_set_field_values(self, hydro_manager: HydroManager, empty_study_880: FileStudy) -> None:
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
        study = FileStudyInterface(empty_study_880)
        # store the area ids
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        for area in areas:
            # get initial values with get_hydro_management_options
            initial_data = hydro_manager.get_hydro_management(study, area).model_dump()

            # simulate changes on area_id case with another tool
            hydro_ini_path = study.file_study.config.study_path / "input" / "hydro" / "hydro.ini"
            with open(hydro_ini_path) as f:
                file_content = f.read()
                file_content = file_content.replace(area, area.lower())

            with open(hydro_ini_path, "w") as f:
                f.write(file_content)

            # make sure that `get_hydro_management_options` retrieve same data as before
            new_data = hydro_manager.get_hydro_management(study, area).model_dump()
            assert initial_data == new_data

            # simulate regular usage by modifying some values
            modified_data = dict(initial_data)
            modified_data["intra_daily_modulation"] = 5.0
            hydro_manager.update_hydro_management(study, HydroManagementUpdate(**modified_data), area)

            # retrieve edited
            new_data = hydro_manager.get_hydro_management(study, area).model_dump()

            # check if the intra daily modulation was modified
            for field, value in new_data.items():
                if field == "intra_daily_modulation":
                    assert initial_data[field] != new_data[field]
                else:
                    assert initial_data[field] == new_data[field]

    @pytest.mark.unit_test
    def test_get_all_hydro_properties(self, hydro_manager: HydroManager, empty_study_880: FileStudy) -> None:
        pass
