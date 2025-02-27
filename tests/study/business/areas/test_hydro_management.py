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

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.tasks.service import TaskJobService
from antarest.login.service import LoginService
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.areas.hydro_management import FIELDS_INFO, ManagementOptionsFormFields
from antarest.study.business.study_interface import StudyInterface
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

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
    @staticmethod
    def create_study_service(
        raw_study_service: RawStudyService,
        generator_matrix_constants: GeneratorMatrixConstants,
        simple_matrix_service: SimpleMatrixService,
    ) -> StudyService:
        # Initialize a study service
        study_service = StudyService(
            raw_study_service=raw_study_service,
            variant_study_service=Mock(spec=VariantStudyService),
            command_context=CommandContext(
                generator_matrix_constants=generator_matrix_constants,
                matrix_service=simple_matrix_service,
            ),
            user_service=Mock(spec=LoginService),
            repository=Mock(StudyMetadataRepository),
            event_bus=Mock(spec=IEventBus),
            task_service=Mock(spec=TaskJobService),
            file_transfer_manager=Mock(spec=FileTransferManager),
            cache_service=Mock(spec=ICache),
            config=Mock(spec=Config),
        )

        return study_service

    @staticmethod
    def create_study_interface(tmp_path: Path) -> StudyInterface:
        study_id = "study_test"
        study_path = tmp_path.joinpath(f"tmp/{study_id}")
        config = build(study_path, study_id)
        tree = FileStudyTree(Mock(spec=ContextServer), config)
        tree.save(hydro_ini_content)

        file_study = Mock(spec=FileStudy, config=config, tree=FileStudyTree(Mock(spec=ContextServer), config))

        study = Mock(spec=StudyInterface, version=860)
        study.get_files.return_value = file_study
        return study

    @pytest.mark.unit_test
    def test_get_field_values(
        self,
        raw_study_service: RawStudyService,
        tmp_path: Path,
        generator_matrix_constants: GeneratorMatrixConstants,
        simple_matrix_service: SimpleMatrixService,
    ) -> None:
        """
        Set up:
            Create a study service, a study and some areas with different letter cases.
        Test:
            Check if `get_field_values` returns the right values
        """
        # retrieve setup data
        study_service = self.create_study_service(raw_study_service, generator_matrix_constants, simple_matrix_service)

        study = self.create_study_interface(tmp_path)

        # add som areas
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        # gather initial data of the area
        for area in areas:
            # get actual value
            data = study_service.hydro_manager.get_field_values(study, area).dict()

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

    @pytest.mark.unit_test
    def test_set_field_values(
        self,
        raw_study_service: RawStudyService,
        tmp_path: Path,
        generator_matrix_constants,
        simple_matrix_service,
    ) -> None:
        """
        Set up:
            Create a study service, study and some areas with different letter cases

        Test:
            Get initial data
            Edit one field (intra_daily_modulation)
            Check if the field was successfully edited for each area
        """
        # create a study service
        study_service = self.create_study_service(raw_study_service, generator_matrix_constants, simple_matrix_service)

        # create a study
        study = self.create_study_interface(tmp_path)

        # store the area ids
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        for area in areas:
            # get initial values with get_field_values
            initial_data = study_service.hydro_manager.get_field_values(study, area).dict()

            # set multiple values with set_field_values
            initial_data["intra_daily_modulation"] = 5
            new_field_values = ManagementOptionsFormFields(**initial_data)
            study_service.hydro_manager.set_field_values(study, new_field_values, area)

            # retrieve edited
            new_data = study_service.hydro_manager.get_field_values(study, area).dict()

            # check if the intra daily modulation was modified
            for field, value in new_data.items():
                if field == "intra_daily_modulation":
                    assert initial_data[field] != new_data[field]
                    assert initial_data[field] == 5
                else:
                    assert initial_data[field] == new_data[field]
