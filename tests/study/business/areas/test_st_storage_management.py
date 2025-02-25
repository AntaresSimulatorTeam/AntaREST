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

import io
import re
import typing as t
from unittest.mock import Mock

import numpy as np
import pytest
from pydantic import ValidationError

from antarest.core.exceptions import AreaNotFound, STStorageConfigNotFound, STStorageMatrixNotFound, STStorageNotFound
from antarest.core.serde.ini_reader import IniReader
from antarest.study.business.areas.st_storage_management import STStorageManager, STStorageUpdate
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    STStorageGroup,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree

# noinspection SpellCheckingInspection
LIST_INI = """
[storage1]
name = Storage1
group = Battery
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.94
initialleveloptim = true

[storage2]
name = Storage2
group = PSP_closed
injectionnominalcapacity = 2000
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.78
initiallevel = 0.5

[storage3]
name = Storage3
group = PSP_closed
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 21000
efficiency = 0.72
initiallevel = 1
"""

LIST_CFG = IniReader().read(io.StringIO(LIST_INI))

ALL_STORAGES = {
    "west": {"list": LIST_CFG},
    "east": {"list": {}},
}

GEN = np.random.default_rng(1000)


def create_study_interface(tree: FileStudyTree) -> StudyInterface:
    """
    Creates a mock study interface which returns the provided study tree.
    """
    file_study = Mock(spec=FileStudy)
    file_study.tree = tree
    study = Mock(StudyInterface)
    study.get_files.return_value = file_study
    study.version = 860
    return study


class TestSTStorageManager:
    def test_get_all_storages__nominal_case(
        self,
        st_storage_manager: STStorageManager,
    ) -> None:
        """
        This unit test is to verify the behavior of the `get_all_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage lists
        for each area, based on a specific configuration.
        """
        # The study must be fetched from the database
        manager = st_storage_manager

        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=ALL_STORAGES),
            )
        )

        # Given the following arguments

        # run
        all_storages = manager.get_all_storages_props(study)

        # Check
        actual = {
            area_id: [form.model_dump(by_alias=True) for form in clusters_by_ids.values()]
            for area_id, clusters_by_ids in all_storages.items()
        }
        expected = {
            "west": [
                {
                    "id": "storage1",
                    "enabled": None,
                    "group": STStorageGroup.BATTERY,
                    "name": "Storage1",
                    "injectionNominalCapacity": 1500.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 20000.0,
                    "efficiency": 0.94,
                    "initialLevel": 0.5,
                    "initialLevelOptim": True,
                },
                {
                    "id": "storage2",
                    "enabled": None,
                    "group": STStorageGroup.PSP_CLOSED,
                    "name": "Storage2",
                    "injectionNominalCapacity": 2000.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 20000.0,
                    "efficiency": 0.78,
                    "initialLevel": 0.5,
                    "initialLevelOptim": False,
                },
                {
                    "id": "storage3",
                    "enabled": None,
                    "group": STStorageGroup.PSP_CLOSED,
                    "name": "Storage3",
                    "injectionNominalCapacity": 1500.0,
                    "withdrawalNominalCapacity": 1500.0,
                    "reservoirCapacity": 21000.0,
                    "efficiency": 0.72,
                    "initialLevel": 1.0,
                    "initialLevelOptim": False,
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
                "enabled": None,
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
                "enabled": None,
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
                "enabled": None,
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
            "enabled": None,
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
        ini_file_node = IniFileNode(context=Mock(), config=Mock())
        file_study = Mock(spec=FileStudy)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG),
            get_node=Mock(return_value=ini_file_node),
        )

        mock_config = Mock(spec=FileStudyTreeConfig, study_id="id", version=STUDY_VERSION_8_6)
        file_study.config = mock_config

        st_storage = STStorageConfig(
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
        file_study.tree.get.return_value = LIST_CFG["storage1"]
        st_storage_output = manager.update_storage(study, area_id="West", storage_id="storage1", cluster_data=edit_form)

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

    def test_get_matrix__nominal_case(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_matrix` method returns the expected storage matrix
        for a specific study, area, storage ID, and Time Series combination.
        """
        # Prepare the mocks
        array = GEN.random((8760, 1)) * 1000
        expected = {
            "index": list(range(8760)),
            "columns": [0],
            "data": array.tolist(),
        }
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=expected),
            )
        )

        # Run the method being tested
        matrix = st_storage_manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")

        # Assert that the returned storage fields match the expected fields
        actual = matrix.model_dump(by_alias=True)
        assert actual == expected

    def test_get_matrix__config_not_found(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class when the time series is not found.

        This test verifies that the `get_matrix` method raises an `STStorageNotFound`
        exception when the configuration for the provided study, area, time series,
        and storage ID combination is not found.
        """
        # Prepare the mocks
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(side_effect=KeyError("Oops!")),
            )
        )

        # Run the method being tested and expect an exception
        with pytest.raises(STStorageMatrixNotFound, match="not found") as ctx:
            st_storage_manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")

        # ensure the error message contains at least the study ID, area ID and storage ID
        err_msg = str(ctx.value)
        assert "storage1" in err_msg
        assert "inflows" in err_msg

    def test_get_matrix__invalid_matrix(self, st_storage_manager: STStorageManager) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class when the time series is not found.

        This test verifies that the `get_matrix` method raises an `STStorageNotFound`
        exception when the configuration for the provided study, area, time series,
        and storage ID combination is not found.
        """
        # Prepare the mocks
        array = GEN.random((365, 1)) * 1000
        matrix = {
            "index": list(range(365)),
            "columns": [0],
            "data": array.tolist(),
        }
        study = create_study_interface(
            Mock(
                spec=FileStudyTree,
                get=Mock(return_value=matrix),
            )
        )

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("time series must have shape (8760, 1)"),
        ):
            st_storage_manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")

    # noinspection SpellCheckingInspection
    def test_validate_matrices__nominal(self, st_storage_manager: STStorageManager) -> None:
        # prepare some random matrices, insuring `lower_rule_curve` <= `upper_rule_curve`
        matrices = {
            "pmax_injection": GEN.random((8760, 1)),
            "pmax_withdrawal": GEN.random((8760, 1)),
            "lower_rule_curve": GEN.random((8760, 1)) / 2,
            "upper_rule_curve": GEN.random((8760, 1)) / 2 + 0.5,
            "inflows": GEN.random((8760, 1)) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: t.Sequence[str], **_: t.Any) -> t.MutableMapping[str, t.Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        file_study = Mock(spec=FileStudy)
        file_study.tree = Mock(spec=FileStudyTree, get=tree_get)
        study = Mock(StudyInterface)
        study.get_files.return_value = file_study
        study.version = 860

        # Given the following arguments, the validation shouldn't raise any exception
        assert st_storage_manager.validate_matrices(study, area_id="West", storage_id="storage1")

    # noinspection SpellCheckingInspection
    def test_validate_matrices__out_of_bound(
        self,
        st_storage_manager: STStorageManager,
    ) -> None:
        # prepare some random matrices, insuring `lower_rule_curve` <= `upper_rule_curve`
        matrices = {
            "pmax_injection": GEN.random((8760, 1)) * 2 - 0.5,  # out of bound
            "pmax_withdrawal": GEN.random((8760, 1)) * 2 - 0.5,  # out of bound
            "lower_rule_curve": GEN.random((8760, 1)) * 2 - 0.5,  # out of bound
            "upper_rule_curve": GEN.random((8760, 1)) * 2 - 0.5,  # out of bound
            "inflows": GEN.random((8760, 1)) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: t.Sequence[str], **_: t.Any) -> t.MutableMapping[str, t.Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        study = create_study_interface(Mock(spec=FileStudyTree, get=tree_get))

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("4 validation errors"),
        ) as ctx:
            st_storage_manager.validate_matrices(study, area_id="West", storage_id="storage1")
        assert ctx.value.error_count() == 4
        for error in ctx.value.errors():
            assert error["type"] == "value_error"
            assert error["msg"] == "Value error, Matrix values should be between 0 and 1"
            assert error["loc"][0] in ["upper_rule_curve", "lower_rule_curve", "pmax_withdrawal", "pmax_injection"]

    # noinspection SpellCheckingInspection
    def test_validate_matrices__rule_curve(self, st_storage_manager: STStorageManager) -> None:
        # prepare some random matrices, not respecting `lower_rule_curve` <= `upper_rule_curve`
        upper_curve = np.zeros((8760, 1))
        lower_curve = np.ones((8760, 1))
        matrices = {
            "pmax_injection": GEN.random((8760, 1)),
            "pmax_withdrawal": GEN.random((8760, 1)),
            "lower_rule_curve": lower_curve,
            "upper_rule_curve": upper_curve,
            "inflows": GEN.random((8760, 1)) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: t.Sequence[str], **_: t.Any) -> t.MutableMapping[str, t.Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        study = create_study_interface(Mock(spec=FileStudyTree, get=tree_get))

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("1 validation error"),
        ) as ctx:
            st_storage_manager.validate_matrices(study, area_id="West", storage_id="storage1")
        error = ctx.value.errors()[0]
        assert error["type"] == "value_error"
        assert (
            error["msg"]
            == "Value error, Each 'lower_rule_curve' value must be lower or equal to each 'upper_rule_curve'"
        )
