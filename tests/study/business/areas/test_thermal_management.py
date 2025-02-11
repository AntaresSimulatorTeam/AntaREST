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

import datetime
import re
import shutil
import uuid
import zipfile
from pathlib import Path

import pytest
from sqlalchemy.orm.session import Session  # type: ignore

from antarest.core.exceptions import CommandApplicationError
from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, User
from antarest.study.business.areas.thermal_management import ThermalClusterCreation, ThermalClusterInput, ThermalManager
from antarest.study.model import RawStudy, Study, StudyAdditionalData, StudyContentStatus
from antarest.study.service import create_thermal_manager
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
)
from antarest.study.storage.storage_service import StudyStorageService
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


@pytest.fixture(name="zip_legacy_path")
def zip_legacy_path_fixture(tmp_path: Path) -> Path:
    target_dir = tmp_path.joinpath("resources")
    target_dir.mkdir()
    resource_zip = ASSETS_DIR.joinpath("thermal_management/study_legacy.zip")
    shutil.copy2(resource_zip, target_dir)
    return target_dir.joinpath(resource_zip.name)


@pytest.fixture(name="metadata_legacy")
def metadata_legacy_fixture(tmp_path: Path, zip_legacy_path: Path) -> RawStudy:
    with zipfile.ZipFile(zip_legacy_path, mode="r") as zf:
        content = zf.read("study.antares").decode("utf-8")
        config = dict(re.findall(r"^(\w+)\s*=\s*(.*?)$", content, flags=re.I | re.M))

    workspace_dir = tmp_path.joinpath("studies")
    workspace_dir.mkdir()

    # noinspection PyArgumentList,SpellCheckingInspection
    metadata = RawStudy(
        id=str(uuid.uuid4()),
        name=config["caption"],
        version=config["version"],
        author=config["author"],
        created_at=datetime.datetime.fromtimestamp(int(config["created"]), datetime.timezone.utc),
        updated_at=datetime.datetime.fromtimestamp(int(config["lastsave"]), datetime.timezone.utc),
        public_mode=PublicMode.FULL,
        workspace="default",
        path=str(workspace_dir.joinpath(config["caption"])),
        content_status=StudyContentStatus.VALID,
        additional_data=StudyAdditionalData(author=config["author"]),
    )

    return metadata


# noinspection PyArgumentList
@pytest.fixture(name="study_legacy_uuid")
def study_legacy_uuid_fixture(
    zip_legacy_path: Path,
    metadata_legacy: RawStudy,
    study_storage_service: StudyStorageService,
    db_session: Session,
) -> str:
    study_id = metadata_legacy.id
    metadata_legacy.user = User(id=1, name="admin")
    metadata_legacy.groups = [Group(id="my-group", name="group")]
    db_session.add(metadata_legacy)
    db_session.commit()

    with db_session:
        metadata = db_session.query(Study).get(study_id)
        with open(zip_legacy_path, mode="rb") as fd:
            study_storage_service.raw_study_service.import_study(metadata, fd)

    return study_id


class TestThermalManager:
    def test_get_cluster__study_legacy(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_legacy_uuid: str,
    ):
        """
        Given a legacy study with a thermal cluster,
        When we get the cluster,
        Then we should get the cluster properties with the correct name and ID.
        Every property related to version 860 or above should be None.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_legacy_uuid)

        # Given the following arguments
        manager = create_thermal_manager(study_storage_service)

        # Run the method being tested
        form = manager.get_cluster(study, area_id="north", cluster_id="2 avail and must 1")

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
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_legacy_uuid: str,
    ):
        """
        Given a legacy study with thermal clusters,
        When we get the clusters,
        Then we should get all cluster properties with the correct names and IDs.
        Every property related to version 860 or above should be None.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_legacy_uuid)

        # Given the following arguments
        manager = create_thermal_manager(study_storage_service)

        # Run the method being tested
        groups = manager.get_clusters(study, area_id="north")

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
        study_storage_service: StudyStorageService,
        study_legacy_uuid: str,
    ):
        """
        Given a legacy study,
        When we create a new thermal cluster,
        Then we should get the cluster properties with the correct name and ID.
        Every property related to version 860 or above should be None.
        """
        with db():
            # The study must be fetched from the database
            study: RawStudy = db.session.query(Study).get(study_legacy_uuid)

            # Given the following arguments
            manager = create_thermal_manager(study_storage_service)

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
            form = manager.create_cluster(study, area_id="north", cluster_data=cluster_data)

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
        study_storage_service: StudyStorageService,
        study_legacy_uuid: str,
    ):
        with db():
            # The study must be fetched from the database
            study: RawStudy = db.session.query(Study).get(study_legacy_uuid)

            # Given the following arguments
            manager = create_thermal_manager(study_storage_service)

            # When some properties of the cluster are updated
            cluster_data = ThermalClusterInput(name="New name", nominalCapacity=2000)
            manager.update_cluster(study, area_id="north", cluster_id="2 avail and must 1", cluster_data=cluster_data)

            # Assert that the returned fields match the expected fields
            form = manager.get_cluster(study, area_id="north", cluster_id="2 avail and must 1")
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
        study_storage_service: StudyStorageService,
        study_legacy_uuid: str,
    ):
        with db():
            # The study must be fetched from the database
            study: RawStudy = db.session.query(Study).get(study_legacy_uuid)

            # Given the following arguments
            manager = create_thermal_manager(study_storage_service)

            # When the clusters are deleted
            manager.delete_clusters(study, area_id="north", cluster_ids=["2 avail and must 1", "on and must 2"])

            # Assert that the returned fields match the expected fields
            groups = manager.get_clusters(study, area_id="north")
            actual = [form.id for form in groups]
            expected = ["2 avail and must 2"]
            assert actual == expected

            # A second attempt should raise an error
            with pytest.raises(CommandApplicationError):
                manager.delete_clusters(study, area_id="north", cluster_ids=["2 avail and must 1"])
