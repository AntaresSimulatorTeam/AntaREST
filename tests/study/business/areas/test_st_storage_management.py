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


import pytest

from antarest.core.exceptions import ChildNotFoundError, STStorageNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.business.model.sts_model import (
    STStorageAdditionalConstraintCreation,
    STStorageCreation,
    STStorageGroup,
    STStorageUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study, file_study_interface

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
            "allowOverflow": True,
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
            "allowOverflow": False,
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
            "allowOverflow": False,
        },
    ],
}


@pytest.fixture
def manager(matrix_service: ISimpleMatrixService, command_context: CommandContext) -> STStorageManager:
    return STStorageManager(command_context)


def _set_up_study(study: StudyInterface, command_context: CommandContext) -> None:
    study_data = study.get_files()
    dao = build_dao_from_file_study(study_data, command_context)
    # Create 2 areas
    output = CreateArea(command_context=command_context, area_name="fr", study_version=study.version).apply(dao)
    assert output.status
    output = CreateArea(command_context=command_context, area_name="DE", study_version=study.version).apply(dao)
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
    output = cmd.apply(dao)
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
    output = cmd.apply(dao)
    assert output.status

    cmd = CreateSTStorage(
        command_context=command_context,
        area_id="de",
        parameters=STStorageCreation(
            name="StorageDE",
            efficiency=0.46,
            efficiency_withdrawal=0.47,
            penalize_variation_injection=True,
            allow_overflow=True,
        ),
        study_version=study.version,
    )
    output = cmd.apply(dao)
    assert output.status


@pytest.fixture
def study_interface(
    matrix_service: ISimpleMatrixService, empty_study_930: FileStudy, command_context: CommandContext
) -> StudyInterface:
    study_interface = file_study_interface(empty_study_930)
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


def test_delete_storages_from_sc_builder(manager: STStorageManager, study_interface: StudyInterface) -> None:
    # Create 3 short-term storage additional constraints
    c1 = STStorageAdditionalConstraintCreation(name="c1")
    c2 = STStorageAdditionalConstraintCreation(name="c2")
    c3 = STStorageAdditionalConstraintCreation(name="c3")
    manager.create_additional_constraints(study_interface, "fr", "storage1", [c1])
    manager.create_additional_constraints(study_interface, "fr", "storage2", [c2])
    manager.create_additional_constraints(study_interface, "de", "storagede", [c3])
    # Fill the scenario-builder
    file_study = study_interface.get_files()
    scenario_builder = {
        "Default Ruleset": {
            # Short-term storage part
            "sts,fr,1,storage1": 4,
            "sts,fr,1,storage2": 3,
            "sts,de,1,storagede": 2,
            # Additional constraints part
            "sta,fr,1,storage1,c1": 11,
            "sta,fr,1,storage2,c2": 12,
            "sta,de,1,storagede,c3": 13,
        }
    }
    file_study.tree.save(scenario_builder, ["settings", "scenariobuilder"])

    # Remove the additional constraint `c3`. Its line only should disappear
    manager.delete_additional_constraints(study_interface, "de", "storagede", ["c3"])
    sc_builder = file_study.tree.get(["settings", "scenariobuilder", "Default Ruleset"])
    assert sc_builder == {
        "sts,fr,1,storage1": 4,
        "sts,fr,1,storage2": 3,
        "sts,de,1,storagede": 2,
        "sta,fr,1,storage1,c1": 11,
        "sta,fr,1,storage2,c2": 12,
    }

    # Remove the sts `storagede`. Its line only should disappear
    manager.delete_storages(study_interface, "de", ["storagede"])
    sc_builder = file_study.tree.get(["settings", "scenariobuilder", "Default Ruleset"])
    assert sc_builder == {
        "sts,fr,1,storage1": 4,
        "sts,fr,1,storage2": 3,
        "sta,fr,1,storage1,c1": 11,
        "sta,fr,1,storage2,c2": 12,
    }

    # Remove the sts `storage1`. 2 lines should disappear, his one and the one concerning its constraint
    manager.delete_storages(study_interface, "fr", ["storage1"])
    sc_builder = file_study.tree.get(["settings", "scenariobuilder", "Default Ruleset"])
    assert sc_builder == {
        "sts,fr,1,storage2": 3,
        "sta,fr,1,storage2,c2": 12,
    }

    # Remove the area `fr`. 2 lines should disappear as they concern objects inside area `fr`.
    cmd = RemoveArea(command_context=manager._command_context, id="fr", study_version=file_study.config.version)
    output = cmd.apply(file_study)
    assert output.status
    sc_builder = file_study.tree.get(["settings", "scenariobuilder", "Default Ruleset"])
    assert sc_builder == {}
