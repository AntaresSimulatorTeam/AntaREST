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
import copy

import pytest
from pydantic import ValidationError

from antarest.study.business.areas.hydro_management import HydroManager
from antarest.study.business.model.hydro_model import (
    HydroManagement,
    HydroManagementUpdate,
    HydroProperties,
    InflowStructure,
    InflowStructureUpdate,
)
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
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
        study.file_study.tree.save(hydro_ini_content)
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
        study.file_study.tree.save(hydro_ini_content)
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

            # Ensures updating with a v9.2 field fails
            with pytest.raises(
                ValidationError,
                match="You cannot fill the parameter `overflow_spilled_cost_difference` before the v9.2",
            ):
                hydro_manager.update_hydro_management(
                    study, HydroManagementUpdate(overflow_spilled_cost_difference=0.3), area
                )

    @pytest.mark.unit_test
    def test_get_all_hydro_properties(
        self,
        hydro_manager: HydroManager,
        empty_study_880: FileStudy,
        empty_study_920: FileStudy,
        command_context: CommandContext,
    ) -> None:
        for file_study in [empty_study_880, empty_study_920]:
            study = FileStudyInterface(file_study)
            study_version = file_study.config.version
            assert hydro_manager.get_all_hydro_properties(study) == {}  # no areas

            # Create 2 areas
            cmd = CreateArea(area_name="FR", command_context=command_context, study_version=study_version)
            cmd.apply(file_study)
            cmd = CreateArea(area_name="be", command_context=command_context, study_version=study_version)
            cmd.apply(file_study)

            # Checks default values
            default_properties = HydroProperties(
                management_options=HydroManagement(
                    inter_daily_breakdown=1.0,
                    intra_daily_modulation=24.0,
                    inter_monthly_breakdown=1.0,
                    reservoir=False,
                    reservoir_capacity=0,
                    follow_load=True,
                    use_water=False,
                    hard_bounds=False,
                    initialize_reservoir_date=0,
                    use_heuristic=True,
                    power_to_level=False,
                    use_leeway=False,
                    leeway_low=1.0,
                    leeway_up=1.0,
                    pumping_efficiency=1.0,
                    overflow_spilled_cost_difference=None,
                ),
                inflow_structure=InflowStructure(inter_monthly_correlation=0.5),
            )
            if study_version == STUDY_VERSION_9_2:
                default_properties.management_options.overflow_spilled_cost_difference = 1
            assert hydro_manager.get_all_hydro_properties(study) == {"fr": default_properties, "be": default_properties}

            # Update properties
            new_properties = HydroManagementUpdate(follow_load=False, intra_daily_modulation=4.1)
            if study_version == STUDY_VERSION_9_2:
                new_properties.overflow_spilled_cost_difference = 0.3
            hydro_manager.update_hydro_management(study, new_properties, "fr")

            new_inflow = InflowStructureUpdate(inter_monthly_correlation=0.2)
            hydro_manager.update_inflow_structure(study, "fr", new_inflow)

            # Checks properties were updated
            new_fr_properties = copy.deepcopy(default_properties)
            new_fr_properties.management_options.follow_load = False
            new_fr_properties.management_options.intra_daily_modulation = 4.1
            if study_version == STUDY_VERSION_9_2:
                new_fr_properties.management_options.overflow_spilled_cost_difference = 0.3
            new_fr_properties.inflow_structure.inter_monthly_correlation = 0.2
            assert hydro_manager.get_all_hydro_properties(study) == {"fr": new_fr_properties, "be": default_properties}
