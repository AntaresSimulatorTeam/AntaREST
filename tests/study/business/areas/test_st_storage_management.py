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

from antarest.core.exceptions import ChildNotFoundError, STStorageNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.areas.st_storage_management import STStorageManager, STStorageUpdate
from antarest.study.business.model.sts_model import STStorageCreation, STStorageGroup
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext

EXPECTED_STORAGES = {
    "de": [
        {
            "efficiency": 0.46,
            "efficiencyWithdrawal": 0.47,
            "enabled": True,
            "group": "other1",
            "id": "storagede",
            "initialLevel": 0.5,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "name": "StorageDE",
            "penalizeVariationInjection": True,
            "penalizeVariationWithdrawal": False,
            "reservoirCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
        }
    ],
    "fr": [
        {
            "efficiency": 0.94,
            "efficiencyWithdrawal": 1.0,
            "enabled": True,
            "group": "battery",
            "id": "storage1",
            "initialLevel": 0.5,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 1500.0,
            "name": "Storage1",
            "penalizeVariationInjection": False,
            "penalizeVariationWithdrawal": False,
            "reservoirCapacity": 20000.0,
            "withdrawalNominalCapacity": 1500.0,
        },
        {
            "efficiency": 1.0,
            "efficiencyWithdrawal": 1.0,
            "enabled": False,
            "group": "my_own_group",
            "id": "storage2",
            "initialLevel": 0.5,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "name": "Storage2",
            "penalizeVariationInjection": False,
            "penalizeVariationWithdrawal": False,
            "reservoirCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
        },
    ],
}


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
    output = CreateArea(command_context=command_context, area_name="fr", study_version=study.version).apply(study_data)
    assert output.status
    output = CreateArea(command_context=command_context, area_name="DE", study_version=study.version).apply(study_data)
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
        study_version=study.version,
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
        study_version=study.version,
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
        study_version=study.version,
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
        assert actual == EXPECTED_STORAGES

    def test_get_st_storages__nominal_case(self, manager: STStorageManager, study_interface: StudyInterface) -> None:
        """
        This unit test is to verify the behavior of the `get_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage list
        based on a specific configuration.
        """

        # run
        groups = manager.get_storages(study_interface, area_id="fr")

        # Check
        actual = [form.model_dump(by_alias=True) for form in groups]
        assert actual == EXPECTED_STORAGES["fr"]

    def test_get_st_storage__nominal_case(self, manager: STStorageManager, study_interface: StudyInterface) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_st_storage` method returns the expected storage fields
        for a specific study, area, and storage ID combination.
        """

        # Run the method being tested
        edit_form = manager.get_storage(study_interface, area_id="de", storage_id="storagedE")

        # Assert that the returned storage fields match the expected fields
        actual = edit_form.model_dump(by_alias=True)
        assert actual == EXPECTED_STORAGES["de"][0]

    # noinspection SpellCheckingInspection
    def test_update_storage__nominal_case(self, manager: STStorageManager, study_interface: StudyInterface) -> None:
        """
        Test the `update_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `update_st_storage` method correctly updates the storage fields
        for a specific study, area, and storage ID combination.
        """

        # Given the following arguments
        edit_form = STStorageUpdate(initial_level=0, initial_level_optim=False, injection_nominal_capacity=2000.0)

        # Test behavior for area not in study
        # noinspection PyTypeChecker
        with pytest.raises(ChildNotFoundError) as ctx:
            manager.update_storage(
                study_interface, area_id="unknown_area", storage_id="storage1", cluster_data=edit_form
            )
        assert "unknown_area" in ctx.value.detail

        # Test behavior for st_storage not in study
        with pytest.raises(STStorageNotFound) as ctx:
            manager.update_storage(study_interface, area_id="fr", storage_id="unknown_storage", cluster_data=edit_form)
        assert "fr" in ctx.value.detail
        assert "unknown_storage" in ctx.value.detail

        # Test behavior for nominal case
        st_storage_output = manager.update_storage(
            study_interface, area_id="fr", storage_id="storage1", cluster_data=edit_form
        )

        assert st_storage_output.initial_level == 0.0
        assert not st_storage_output.initial_level_optim
        assert st_storage_output.injection_nominal_capacity == 2000.0
        assert st_storage_output.efficiency == 0.94  # Asserts this field wasn't modified as we didn't ask to
