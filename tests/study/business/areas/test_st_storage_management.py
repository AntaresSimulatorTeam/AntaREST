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

import pytest

from antarest.core.exceptions import AreaNotFound, STStorageConfigNotFound, STStorageNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.areas.st_storage_management import STStorageManager, STStorageUpdate
from antarest.study.business.model.sts_model import STStorage, STStorageCreation, STStorageGroup
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.fixture
def command_context(matrix_service: ISimpleMatrixService) -> CommandContext:
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    matrix_constants.init_constant_matrices()
    return CommandContext(generator_matrix_constants=matrix_constants, matrix_service=matrix_service)


@pytest.fixture
def manager(matrix_service: ISimpleMatrixService, command_context: CommandContext) -> STStorageManager:
    return STStorageManager(command_context)

def _set_up_study(study: StudyInterface, command_context: CommandContext) -> None:
    study_data = study.get_files()
    # Create 2 areas
    output = CreateArea(command_context=command_context,  area_name="fr", study_version=study.version).apply(study_data)
    assert output.status
    output = CreateArea(command_context=command_context,  area_name="DE", study_version=study.version).apply(study_data)
    assert output.status
    # Create 2 storages in fr area and 1 in DE area
    cmd = CreateSTStorage(
        command_context=command_context,
        area_id="fr",
        parameters=STStorageCreation(
            name="Storage1",
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=1500,
            withdrawal_nominal_capacity=1500,
            reservoir_capacity=20000,
            efficiency=0.94,
            initial_level_optim=True,
        ),
        study_version=study.version
    )
    output = cmd.apply(study_data)
    assert output.status

    cmd = CreateSTStorage(
        command_context=command_context,
        area_id="fr",
        parameters=STStorageCreation(
            name="Storage2",
            group="my_own_group",
            enabled=False,
        ),
        study_version=study.version
    )
    output = cmd.apply(study_data)
    assert output.status

    cmd = CreateSTStorage(
        command_context=command_context,
        area_id="de",
        parameters=STStorageCreation(
            name="StorageDE",
            efficiency=0.46,
            efficiency_withdrawal=0.47,
            penalize_variation_injection=True,
        ),
        study_version=study.version
    )
    output = cmd.apply(study_data)
    assert output.status

@pytest.fixture
def study_interface(matrix_service: ISimpleMatrixService, empty_study_920, command_context) -> StudyInterface:
    study_interface = FileStudyInterface(empty_study_920)
    _set_up_study(study_interface, command_context)
    return study_interface


class TestSTStorageManager:
    def test_get_all_storages__nominal_case(self, manager: STStorageManager, study_interface: StudyInterface) -> None:
        """
        This unit test is to verify the behavior of the `get_all_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage lists
        for each area, based on a specific configuration.
        """

        # Given the following arguments

        # run
        all_storages = manager.get_all_storages_props(study_interface)

        # Check
        actual = {
            area_id: [form.model_dump(by_alias=True) for form in clusters_by_ids.values()]
            for area_id, clusters_by_ids in all_storages.items()
        }
        expected = {
            "west": [
                {
                    "id": "storage1",
                    "group": STStorageGroup.BATTERY,
                    "name": "Storage1",
                    "injectionNominalCapacity": 1500.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 20000.0,
                    "efficiency": 0.94,
                    "initialLevel": 0.5,
                    "initialLevelOptim": True,
                    # v8.8 field
                    "enabled": None,
                    # v9.2 fields
                    "efficiencyWithdrawal": None,
                    "penalizeVariationInjection": None,
                    "penalizeVariationWithdrawal": None,
                },
                {
                    "id": "storage2",
                    "group": STStorageGroup.PSP_CLOSED,
                    "name": "Storage2",
                    "injectionNominalCapacity": 2000.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 20000.0,
                    "efficiency": 0.78,
                    "initialLevel": 0.5,
                    "initialLevelOptim": False,
                    # v8.8 field
                    "enabled": None,
                    # v9.2 fields
                    "efficiencyWithdrawal": None,
                    "penalizeVariationInjection": None,
                    "penalizeVariationWithdrawal": None,
                },
                {
                    "id": "storage3",
                    "group": STStorageGroup.PSP_CLOSED,
                    "name": "Storage3",
                    "injectionNominalCapacity": 1500.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 21000.0,
                    "efficiency": 0.72,
                    "initialLevel": 1.0,
                    "initialLevelOptim": False,
                    # v8.8 field
                    "enabled": None,
                    # v9.2 fields
                    "efficiencyWithdrawal": None,
                    "penalizeVariationInjection": None,
                    "penalizeVariationWithdrawal": None,
                },
            ],
        }
        assert actual == expected

    def test_get_all_storages__config_not_found(self, st_storage_manager: STStorageManager) -> None:
        """
        This test verifies that when the `get_all_storages` method is called
        with a study and the corresponding configuration is not found
        (indicated by the `KeyError` raised by the mock), it correctly
        raises the `STStorageConfigNotFound` exception with the expected error
        message containing the study ID.
        """
        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(side_effect=KeyError("Oops!")),
            )
        )

        # run
        with pytest.raises(STStorageConfigNotFound, match="not found"):
            st_storage_manager.get_all_storages_props(study)

    def test_get_st_storages__nominal_case(self, st_storage_manager: STStorageManager) -> None:
        """
        This unit test is to verify the behavior of the `get_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage list
        based on a specific configuration.
        """

        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=LIST_CFG),
            )
        )

        # run
        groups = st_storage_manager.get_storages(study, area_id="West")

        # Check
        actual = [form.model_dump(by_alias=True) for form in groups]
        expected = [
            {
                "efficiency": 0.94,
                "group": STStorageGroup.BATTERY,
                "id": "storage1",
                "initialLevel": 0.5,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage1",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
                # v8.8 field
                "enabled": None,
                # v9.2 fields
                "efficiencyWithdrawal": None,
                "penalizeVariationInjection": None,
                "penalizeVariationWithdrawal": None,
            },
            {
                "efficiency": 0.78,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage2",
                "initialLevel": 0.5,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 2000.0,
                "name": "Storage2",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
                # v8.8 field
                "enabled": None,
                # v9.2 fields
                "efficiencyWithdrawal": None,
                "penalizeVariationInjection": None,
                "penalizeVariationWithdrawal": None,
            },
            {
                "efficiency": 0.72,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage3",
                "initialLevel": 1,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage3",
                "reservoirCapacity": 21000.0,
                "withdrawalNominalCapacity": 1500.0,
                # v8.8 field
                "enabled": None,
                # v9.2 fields
                "efficiencyWithdrawal": None,
                "penalizeVariationInjection": None,
                "penalizeVariationWithdrawal": None,
            },
        ]
        assert actual == expected

    def test_get_st_storages__config_not_found(self, st_storage_manager: STStorageManager) -> None:
        """
        This test verifies that when the `get_storages` method is called
        with a study and area ID, and the corresponding configuration is not found
        (indicated by the `KeyError` raised by the mock), it correctly
        raises the `STStorageConfigNotFound` exception with the expected error
        message containing the study ID and area ID.
        """
        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(side_effect=KeyError("Oops!")),
            )
        )

        # run
        with pytest.raises(STStorageConfigNotFound, match="not found") as ctx:
            st_storage_manager.get_storages(study, area_id="West")

        # ensure the error message contains at least the study ID and area ID
        err_msg = str(ctx.value)
        assert "West" in err_msg

    def test_get_st_storage__nominal_case(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_st_storage` method returns the expected storage fields
        for a specific study, area, and storage ID combination.
        """

        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=LIST_CFG["storage1"]),
            )
        )

        # Run the method being tested
        edit_form = st_storage_manager.get_storage(study, area_id="West", storage_id="storage1")

        # Assert that the returned storage fields match the expected fields
        actual = edit_form.model_dump(by_alias=True)
        expected = {
            "efficiency": 0.94,
            "group": STStorageGroup.BATTERY,
            "id": "storage1",
            "initialLevel": 0.5,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 1500.0,
            "name": "Storage1",
            "reservoirCapacity": 20000.0,
            "withdrawalNominalCapacity": 1500.0,
            # v8.8 field
            "enabled": None,
            # v9.2 fields
            "efficiencyWithdrawal": None,
            "penalizeVariationInjection": None,
            "penalizeVariationWithdrawal": None,
        }
        assert actual == expected

    # noinspection SpellCheckingInspection
    def test_update_storage__nominal_case(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `update_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `update_st_storage` method correctly updates the storage fields
        for a specific study, area, and storage ID combination.
        """
        manager = st_storage_manager

        # Prepare the mocks
        ini_file_node = IniFileNode(config=Mock())
        file_study = Mock(spec=FileStudy)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG),
            get_node=Mock(return_value=ini_file_node),
        )

        mock_config = Mock(spec=FileStudyTreeConfig, study_id="id", version=STUDY_VERSION_8_6)
        file_study.config = mock_config

        st_storage = STStorage(
            id="storage1",
            name="storage1",
            group=STStorageGroup.OTHER1,
            injection_nominal_capacity=100.0,
            withdrawal_nominal_capacity=100.0,
            reservoir_capacity=100.0,
            efficiency=1.0,
            initial_level=0.5,
            initial_level_optim=True,
        )

        area_west = Area(
            name="West",
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
            st_storages=[st_storage],
        )

        mock_config.areas = {"West": area_west}
        file_study.config = mock_config

        study = FileStudyInterface(file_study)

        # Given the following arguments
        edit_form = STStorageUpdate(initial_level=0, initial_level_optim=False, injection_nominal_capacity=2000.0)

        # Test behavior for area not in study
        # noinspection PyTypeChecker
        file_study.tree.get.return_value = {}
        with pytest.raises((AreaNotFound, STStorageNotFound)) as ctx:
            manager.update_storage(study, area_id="unknown_area", storage_id="storage1", cluster_data=edit_form)
        assert "unknown_area" in ctx.value.detail

        # Test behavior for st_storage not in study
        file_study.tree.get.return_value = {"storage1": LIST_CFG["storage1"]}
        with pytest.raises(STStorageNotFound) as ctx:
            manager.update_storage(study, area_id="West", storage_id="unknown_storage", cluster_data=edit_form)
        assert "West" in ctx.value.detail
        assert "unknown_storage" in ctx.value.detail

        # Test behavior for nominal case
        study.file_study.config.areas = {"west": area_west}
        file_study.tree.get.return_value = LIST_CFG
        st_storage_output = manager.update_storage(study, area_id="west", storage_id="storage1", cluster_data=edit_form)

        assert st_storage_output.initial_level == 0.0
        assert not st_storage_output.initial_level_optim
        assert st_storage_output.injection_nominal_capacity == 2000.0
        assert st_storage_output.efficiency == 1.0

    def test_get_st_storage__config_not_found(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class when the configuration is not found.

        This test verifies that the `get_st_storage` method raises an `STStorageNotFound`
        exception when the configuration for the provided study, area, and storage ID combination is not found.
        """

        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(side_effect=KeyError("Oops!")),
            )
        )
        # Run the method being tested and expect an exception
        with pytest.raises(STStorageNotFound, match="not found") as ctx:
            st_storage_manager.get_storage(study, area_id="West", storage_id="storage1")
        # ensure the error message contains at least the study ID, area ID and storage ID
        err_msg = str(ctx.value)
        assert "storage1" in err_msg
