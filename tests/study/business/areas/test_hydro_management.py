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
<<<<<<< HEAD
import datetime
import os
import uuid
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.business.areas.hydro_management import HydroManager, ManagementOptionsFormFields
from antarest.study.model import RawStudy, Study, StudyContentStatus
=======
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.areas.hydro_management import HydroManager, ManagementOptionsFormFields
from antarest.study.business.study_interface import FileStudyInterface
>>>>>>> dev
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
<<<<<<< HEAD
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
=======
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
>>>>>>> dev

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


<<<<<<< HEAD
@pytest.fixture(name="study_storage_service")
def study_storage_service() -> StudyStorageService:
    """Return a mocked StudyStorageService."""
    return Mock(
        spec=StudyStorageService,
        variant_study_service=Mock(
            spec=VariantStudyService,
            command_factory=Mock(
                spec=CommandFactory,
                command_context=Mock(spec=CommandContext),
            ),
        ),
        get_storage=Mock(return_value=Mock(spec=RawStudyService, get_raw=Mock(spec=FileStudy))),
    )


# noinspection PyArgumentList
@pytest.fixture(name="study_uuid")
def study_uuid_fixture(db_session: Session) -> str:
    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    raw_study = RawStudy(
        id=str(uuid.uuid4()),
        name="Dummy",
        version="860",  # version 860 is required for the storage feature
        author="John Smith",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
        public_mode=PublicMode.FULL,
        owner=user,
        groups=[group],
        workspace="default",
        path="/path/to/study",
        content_status=StudyContentStatus.WARNING,
    )
    db_session.add(raw_study)
    db_session.commit()
    return cast(str, raw_study.id)


@pytest.fixture
def study_tree(tmp_path: Path, study_uuid: str) -> FileStudyTree:
    study_path = tmp_path.joinpath(f"tmp/{study_uuid}")
    study_path.mkdir(parents=True, exist_ok=True)
    config = build(study_path, study_uuid)
    tree = FileStudyTree(Mock(spec=ContextServer), config)
    tree.save(hydro_ini_content)
    return tree


class TestHydroManagement:

    @pytest.mark.unit_test
    def test_get_field_values(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
        study_tree: FileStudyTree,
    ) -> None:
=======
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
>>>>>>> dev
        """
        Set up:
            Retrieve a study service and a study interface
            Create some areas with different letter cases
        Test:
            Check if `get_field_values` returns the right values
        """
<<<<<<< HEAD
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = study_tree

        # Given the following arguments
        hydro_manager = HydroManager(study_storage_service)

=======
>>>>>>> dev
        # add som areas
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        # gather initial data of the area
        for area in areas:
            # get actual value
            data_area_raw = hydro_manager.get_field_values(study, area).model_dump()

            # get values if area_id is in lower case
            data_area_lower = hydro_manager.get_field_values(study, area.lower()).model_dump()

            # get values if area_id is in upper case
            data_area_upper = hydro_manager.get_field_values(study, area.upper()).model_dump()

            # check if the area is retrieved regardless of the letters case
            assert data_area_raw == data_area_lower
            assert data_area_raw == data_area_upper

    @pytest.mark.unit_test
<<<<<<< HEAD
    def test_set_field_values(
        self,
        tmp_path: Path,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
        study_tree: FileStudyTree,
    ) -> None:
=======
    def test_set_field_values(self, tmp_path: Path, hydro_manager: HydroManager, study: FileStudyInterface) -> None:
>>>>>>> dev
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
<<<<<<< HEAD
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = study_tree

        # Given the following arguments
        hydro_manager = HydroManager(study_storage_service)

=======
>>>>>>> dev
        # store the area ids
        areas = ["AreaTest1", "AREATEST2", "area_test_3"]

        for area in areas:
            # get initial values with get_field_values
            initial_data = hydro_manager.get_field_values(study, area).model_dump()

            # simulate changes on area_id case with another tool
            hydro_ini_path = tmp_path.joinpath(f"tmp/{study.id}/input/hydro/hydro.ini")
            with open(hydro_ini_path) as f:
                file_content = f.read()
                file_content = file_content.replace(area, area.lower())

            with open(hydro_ini_path, "w") as f:
                f.write(file_content)

            # make sure that `get_field_values` retrieve same data as before
            new_data = hydro_manager.get_field_values(study, area).model_dump()
            assert initial_data == new_data

            # simulate regular usage by modifying some values
            modified_data = dict(initial_data)
            modified_data["intra_daily_modulation"] = 5.0
            hydro_manager.set_field_values(study, ManagementOptionsFormFields(**modified_data), area)

            # retrieve edited
            new_data = hydro_manager.get_field_values(study, area).model_dump()

            # check if the intra daily modulation was modified
            for field, value in new_data.items():
                if field == "intra_daily_modulation":
                    assert initial_data[field] != new_data[field]
                else:
                    assert initial_data[field] == new_data[field]
