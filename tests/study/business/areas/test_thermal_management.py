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

import zipfile
from pathlib import Path

import pytest

import antarest.study.storage.rawstudy.model.filesystem.config.files
from antarest.core.exceptions import CommandApplicationError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.business.areas.thermal_management import (
    ThermalClusterCreation,
    ThermalClusterUpdate,
    ThermalManager,
)
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
)
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.business.areas.assets import ASSETS_DIR


class TestThermalClusterGroup:
    """
    Tests for the `ThermalClusterGroup` enumeration.
    """

    def test_nominal_case(self):
        """
        When a group is read from a INI file, the group should be the same as the one in the file.
        """
        group = ThermalClusterGroup("gas")  # different case: original is "Gas"
        assert group == ThermalClusterGroup.GAS

    def test_unknown(self):
        """
        When an unknown group is read from a INI file, the group should be `OTHER1`.
        Note that this is the current behavior in Antares Solver.
        """
        group = ThermalClusterGroup("unknown")
        assert group == ThermalClusterGroup.OTHER1

    def test_invalid_type(self):
        """
        When an invalid type is used to create a group, a `ValueError` should be raised.
        """
        with pytest.raises(ValueError):
            ThermalClusterGroup(123)


@pytest.fixture
def study_path(tmp_path: Path) -> Path:
    study_path = tmp_path / "study"
    study_path.mkdir()
    resource_zip = ASSETS_DIR.joinpath("thermal_management/study_legacy.zip")
    with zipfile.ZipFile(resource_zip, "r") as zip_ref:
        zip_ref.extractall(study_path)
    return study_path


def create_file_study(matrix_service: ISimpleMatrixService, study_id: str, path: Path) -> FileStudy:
    context = ContextServer(matrix_service, UriResolverService(matrix_service))
    config = antarest.study.storage.rawstudy.model.filesystem.config.files.build(study_id=study_id, study_path=path)
    tree = FileStudyTree(context, config)
    return FileStudy(config, tree)


@pytest.fixture
def manager(matrix_service: ISimpleMatrixService, study_path) -> ThermalManager:
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    matrix_constants.init_constant_matrices()
    return ThermalManager(CommandContext(generator_matrix_constants=matrix_constants, matrix_service=matrix_service))


@pytest.fixture
def study_interface(matrix_service: ISimpleMatrixService, study_path) -> StudyInterface:
    file_study = create_file_study(matrix_service, study_id="my-study", path=study_path)
    return FileStudyInterface(file_study)


class TestThermalManager:
    def test_get_cluster__study_legacy(self, manager: ThermalManager, study_interface: StudyInterface):
        """
        Given a legacy study with a thermal cluster,
        When we get the cluster,
        Then we should get the cluster properties with the correct name and ID.
        Every property related to version 860 or above should be None.
        """
        # The study must be fetched from the database

        # Run the method being tested
        form = manager.get_cluster(study_interface, area_id="north", cluster_id="2 avail and must 1")

        # Assert that the returned fields match the expected fields
        actual = form.model_dump(by_alias=True)
        expected = {
            "id": "2 avail and must 1",
            "group": ThermalClusterGroup.GAS,
            "name": "2 avail and must 1",
            "enabled": False,
            "unitCount": 100,
            "nominalCapacity": 1000.0,
            "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
            "minStablePower": 0.0,
            "minUpTime": 1,
            "minDownTime": 1,
            "mustRun": True,
            "spinning": 0.0,
            "volatilityForced": 0.0,
            "volatilityPlanned": 0.0,
            "lawForced": LawOption.UNIFORM,
            "lawPlanned": LawOption.UNIFORM,
            "marginalCost": 0.0,
            "spreadCost": 0.0,
            "fixedCost": 0.0,
            "startupCost": 0.0,
            "marketBidCost": 0.0,
            "co2": 7.0,
            # Pollutant values are `None` because they are not defined before version 8.6.
            "nh3": None,
            "so2": None,
            "nox": None,
            "pm25": None,
            "pm5": None,
            "pm10": None,
            "nmvoc": None,
            "op1": None,
            "op2": None,
            "op3": None,
            "op4": None,
            "op5": None,
            # These values are also None as they are defined in v8.7+
            "costGeneration": None,
            "efficiency": None,
            "variableOMCost": None,
        }
        assert actual == expected

    def test_get_clusters__study_legacy(
        self,
        manager: ThermalManager,
        study_interface: StudyInterface,
    ):
        """
        Given a legacy study with thermal clusters,
        When we get the clusters,
        Then we should get all cluster properties with the correct names and IDs.
        Every property related to version 860 or above should be None.
        """
        # Run the method being tested
        groups = manager.get_clusters(study_interface, area_id="north")

        # Assert that the returned fields match the expected fields
        actual = [form.model_dump(by_alias=True) for form in groups]
        expected = [
            {
                "id": "2 avail and must 1",
                "group": ThermalClusterGroup.GAS,
                "name": "2 avail and must 1",
                "enabled": False,
                "unitCount": 100,
                "nominalCapacity": 1000.0,
                "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
                "minStablePower": 0.0,
                "minUpTime": 1,
                "minDownTime": 1,
                "mustRun": True,
                "spinning": 0.0,
                "volatilityForced": 0.0,
                "volatilityPlanned": 0.0,
                "lawForced": LawOption.UNIFORM,
                "lawPlanned": LawOption.UNIFORM,
                "marginalCost": 0.0,
                "spreadCost": 0.0,
                "fixedCost": 0.0,
                "startupCost": 0.0,
                "marketBidCost": 0.0,
                "co2": 7.0,
                "nh3": None,
                "so2": None,
                "nox": None,
                "pm25": None,
                "pm5": None,
                "pm10": None,
                "nmvoc": None,
                "op1": None,
                "op2": None,
                "op3": None,
                "op4": None,
                "op5": None,
                "costGeneration": None,
                "efficiency": None,
                "variableOMCost": None,
            },
            {
                "id": "on and must 2",
                "group": ThermalClusterGroup.HARD_COAL,
                "name": "on and must 2",
                "enabled": True,
                "unitCount": 100,
                "nominalCapacity": 2300.0,
                "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
                "minStablePower": 0.0,
                "minUpTime": 1,
                "minDownTime": 1,
                "mustRun": True,
                "spinning": 0.0,
                "volatilityForced": 0.0,
                "volatilityPlanned": 0.0,
                "lawForced": LawOption.UNIFORM,
                "lawPlanned": LawOption.UNIFORM,
                "marginalCost": 0.0,
                "spreadCost": 0.0,
                "fixedCost": 0.0,
                "startupCost": 0.0,
                "marketBidCost": 0.0,
                "co2": 0.0,
                "nh3": None,
                "so2": None,
                "nox": None,
                "pm25": None,
                "pm5": None,
                "pm10": None,
                "nmvoc": None,
                "op1": None,
                "op2": None,
                "op3": None,
                "op4": None,
                "op5": None,
                "costGeneration": None,
                "efficiency": None,
                "variableOMCost": None,
            },
            {
                "id": "2 avail and must 2",
                "group": ThermalClusterGroup.GAS,
                "name": "2 avail and must 2",
                "enabled": False,
                "unitCount": 100,
                "nominalCapacity": 1500.0,
                "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
                "minStablePower": 0.0,
                "minUpTime": 1,
                "minDownTime": 1,
                "mustRun": True,
                "spinning": 0.0,
                "volatilityForced": 0.0,
                "volatilityPlanned": 0.0,
                "lawForced": LawOption.UNIFORM,
                "lawPlanned": LawOption.UNIFORM,
                "marginalCost": 0.0,
                "spreadCost": 0.0,
                "fixedCost": 0.0,
                "startupCost": 0.0,
                "marketBidCost": 0.0,
                "co2": 0.0,
                "nh3": None,
                "so2": None,
                "nox": None,
                "pm25": None,
                "pm5": None,
                "pm10": None,
                "nmvoc": None,
                "op1": None,
                "op2": None,
                "op3": None,
                "op4": None,
                "op5": None,
                "costGeneration": None,
                "efficiency": None,
                "variableOMCost": None,
            },
        ]
        assert actual == expected

    def test_create_cluster__study_legacy(
        self,
        manager: ThermalManager,
        study_interface: StudyInterface,
    ):
        """
        Given a legacy study,
        When we create a new thermal cluster,
        Then we should get the cluster properties with the correct name and ID.
        Every property related to version 860 or above should be None.
        """
        # Given the following arguments
        props = dict(
            name="New Cluster",
            group=ThermalClusterGroup.NUCLEAR,
            enabled=True,
            unitCount=350,
            nominalCapacity=1000,
            genTs=LocalTSGenerationBehavior.USE_GLOBAL,
            minStablePower=0,
            minUpTime=15,
            minDownTime=20,
            co2=12.59,
        )
        cluster_data = ThermalClusterCreation(**props)
        form = manager.create_cluster(study_interface, area_id="north", cluster_data=cluster_data)

        # Assert that the returned fields match the expected fields
        actual = form.model_dump(by_alias=True)
        expected = {
            "co2": 12.59,
            "enabled": True,
            "fixedCost": 0.0,
            "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
            "group": ThermalClusterGroup.NUCLEAR,
            "id": "New Cluster",
            "lawForced": LawOption.UNIFORM,
            "lawPlanned": LawOption.UNIFORM,
            "marginalCost": 0.0,
            "marketBidCost": 0.0,
            "minDownTime": 20,
            "minStablePower": 0.0,
            "minUpTime": 15,
            "mustRun": False,
            "name": "New Cluster",
            "nh3": None,
            "nmvoc": None,
            "nominalCapacity": 1000.0,
            "nox": None,
            "op1": None,
            "op2": None,
            "op3": None,
            "op4": None,
            "op5": None,
            "pm10": None,
            "pm25": None,
            "pm5": None,
            "so2": None,
            "costGeneration": None,
            "efficiency": None,
            "variableOMCost": None,
            "spinning": 0.0,
            "spreadCost": 0.0,
            "startupCost": 0.0,
            "unitCount": 350,
            "volatilityForced": 0.0,
            "volatilityPlanned": 0.0,
        }
        assert actual == expected

    def test_update_cluster(
        self,
        manager: ThermalManager,
        study_interface: StudyInterface,
    ):
        # When some properties of the cluster are updated
        cluster_data = ThermalClusterUpdate(name="New name", nominalCapacity=2000)
        manager.update_cluster(
            study_interface, area_id="north", cluster_id="2 avail and must 1", cluster_data=cluster_data
        )

        # Assert that the returned fields match the expected fields
        form = manager.get_cluster(study_interface, area_id="north", cluster_id="2 avail and must 1")
        actual = form.model_dump(by_alias=True)
        expected = {
            "id": "2 avail and must 1",
            "group": ThermalClusterGroup.GAS,
            "name": "New name",
            "enabled": False,
            "unitCount": 100,
            "nominalCapacity": 2000.0,
            "genTs": LocalTSGenerationBehavior.USE_GLOBAL,
            "minStablePower": 0.0,
            "minUpTime": 1,
            "minDownTime": 1,
            "mustRun": True,
            "spinning": 0.0,
            "volatilityForced": 0.0,
            "volatilityPlanned": 0.0,
            "lawForced": LawOption.UNIFORM,
            "lawPlanned": LawOption.UNIFORM,
            "marginalCost": 0.0,
            "spreadCost": 0.0,
            "fixedCost": 0.0,
            "startupCost": 0.0,
            "marketBidCost": 0.0,
            "co2": 7.0,
            # Pollutant values are `None` because they are not defined before version 8.6.
            "nh3": None,
            "so2": None,
            "nox": None,
            "pm25": None,
            "pm5": None,
            "pm10": None,
            "nmvoc": None,
            "op1": None,
            "op2": None,
            "op3": None,
            "op4": None,
            "op5": None,
            # These values are also None as they are defined in v8.7+
            "costGeneration": None,
            "efficiency": None,
            "variableOMCost": None,
        }
        assert actual == expected

    def test_delete_clusters(
        self,
        manager: ThermalManager,
        study_interface: StudyInterface,
    ):
        # When the clusters are deleted
        manager.delete_clusters(study_interface, area_id="north", cluster_ids=["2 avail and must 1", "on and must 2"])

        # Assert that the returned fields match the expected fields
        groups = manager.get_clusters(study_interface, area_id="north")
        actual = [form.id for form in groups]
        expected = ["2 avail and must 2"]
        assert actual == expected

        # A second attempt should raise an error
        with pytest.raises(CommandApplicationError):
            manager.delete_clusters(study_interface, area_id="north", cluster_ids=["2 avail and must 1"])
