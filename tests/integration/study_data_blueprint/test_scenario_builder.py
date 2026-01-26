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
from pathlib import Path

import pytest
from antares.study.version import StudyVersion
from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import StudyPermissionType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import current_user_context
from antarest.study.business.model.area_model import AreaCreation
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.scenario_builder_model import AreaItemsScenarios, AreaScenarios
from antarest.study.business.model.sts_model import STStorageAdditionalConstraintCreation, STStorageCreation
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3, StorageMode
from antarest.study.service import StudyService


def _initialize_study(study_service: StudyService, study_id: str, version: StudyVersion) -> None:
    study_service.create_area(study_id, AreaCreation(name="fr"))
    study_service.create_area(study_id, AreaCreation(name="be"))
    study_service.create_link(study_id, Link(area1="be", area2="fr"))
    study = study_service.check_study_access(study_id, StudyPermissionType.WRITE)
    study_interface = study_service.get_study_interface(study)
    study_service.thermal_manager.create_cluster(
        study_interface, "fr", ThermalClusterCreation(name="Nuclear", unit_count=10, nominal_capacity=1000)
    )
    study_service.st_storage_manager.create_storage(study_interface, "fr", STStorageCreation(name="Battery"))
    if version > STUDY_VERSION_9_2:
        study_service.st_storage_manager.create_additional_constraints(
            study_interface, "fr", "battery", [STStorageAdditionalConstraintCreation(name="C1")]
        )


def create_raw_study(study_service: StudyService, version: StudyVersion) -> str:
    """
    Creates a study with:
     - 2 areas be and fr
     - one link between them
     - one thermal cluster in fr, named Nuclear

     Returns its id.
    """

    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study_id = study_service.create_study(
            study_name="test", version=version, group_ids=[], storage_mode=StorageMode.FILESYSTEM
        )
        _initialize_study(study_service, study_id, version)
        return study_id


def create_variant_study(study_service: StudyService, version: StudyVersion) -> str:
    """
    Creates a study with:
     - 2 areas be and fr
     - one link between them
     - one thermal cluster in fr, named Nuclear

     Returns its id.
    """
    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study_id = study_service.create_study(
            study_name="test", version=version, group_ids=[], storage_mode=StorageMode.FILESYSTEM
        )
        _initialize_study(study_service, study_id, version)
        variant_service = study_service.storage_service.variant_study_service
        variant_study = variant_service.create_variant_study(study_id, name="variant")
        return variant_study.id


@pytest.mark.parametrize("variant", [False, True])
def test_scenario_builder_nominal_case(variant: bool, study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    if variant:
        study_id = create_variant_study(study_service, STUDY_VERSION_9_3)
    else:
        study_id = create_raw_study(study_service, STUDY_VERSION_9_3)

    # Load tests

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/load")
    assert res.status_code == 200
    assert res.json() == {"load": {"be": {"0": ""}, "fr": {"0": ""}}}

    scenarios: AreaScenarios = {"be": {"0": 2}}
    res = client.put(f"/v1/studies/{study_id}/config/scenariobuilder/load", json={"load": scenarios})
    assert res.status_code == 200, res.json()

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/load")
    assert res.status_code == 200
    assert res.json() == {"load": {"be": {"0": 2}, "fr": {"0": ""}}}

    # Thermal clusters tests

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/thermal")
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"0": ""}}}}

    scenarios: AreaItemsScenarios = {"be": {}, "fr": {"nuclear": {"0": 2}}}
    res = client.put(f"/v1/studies/{study_id}/config/scenariobuilder/thermal", json={"thermal": scenarios})
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"0": 2}}}}

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/thermal")
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"0": 2}}}}

    # Storages additional constraints

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/shortTermStorageAdditionalConstraints")
    assert res.status_code == 200
    assert res.json() == {"shortTermStorageAdditionalConstraints": {"be": {}, "fr": {"battery": {"c1": {"0": ""}}}}}

    sts_ac_scenarios = {"fr": {"battery": {"c1": {"0": 2}}}}
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder/shortTermStorageAdditionalConstraints",
        json={"shortTermStorageAdditionalConstraints": sts_ac_scenarios},
    )
    assert res.status_code == 200
    assert res.json() == {"shortTermStorageAdditionalConstraints": {"fr": {"battery": {"c1": {"0": 2}}}}}

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/shortTermStorageAdditionalConstraints")
    assert res.status_code == 200
    assert res.json() == {"shortTermStorageAdditionalConstraints": {"be": {}, "fr": {"battery": {"c1": {"0": 2}}}}}

    # Hydro tests

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/hydroInitialLevels")
    assert res.status_code == 200
    assert res.json() == {"hydroInitialLevels": {"be": {"0": ""}, "fr": {"0": ""}}}

    hydro_scenarios = {"be": {"0": 0.5}}
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder/hydroInitialLevels",
        json={"hydroInitialLevels": hydro_scenarios},
    )
    assert res.status_code == 200, res.json()

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/hydroInitialLevels")
    assert res.status_code == 200
    assert res.json() == {"hydroInitialLevels": {"be": {"0": 0.5}, "fr": {"0": ""}}}


@pytest.mark.parametrize("version", [STUDY_VERSION_8_8, STUDY_VERSION_9_2])
def test_scenario_builder_version(
    version: StudyVersion, study_service: StudyService, admin_client: TestClient, tmp_path: Path
) -> None:
    client = admin_client
    study_id = create_raw_study(study_service, version)

    # Ensures we cannot ask for scenario types that did not exist in the study version

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/hydroFinalLevels")
    if version == STUDY_VERSION_8_8:
        assert res.status_code == 422
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == "Invalid scenario types ['hydroFinalLevels'] provided for version 8.8"
    else:
        assert res.status_code == 200
        assert res.json() == {"hydroFinalLevels": {"fr": {"0": ""}, "be": {"0": ""}}}

    for scenario_type in ["shortTermStorageAdditionalConstraints", "shortTermStorageInflows"]:
        res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/{scenario_type}")
        assert res.status_code == 422
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == f"Invalid scenario types ['{scenario_type}'] provided for version {version}"

    # The same goes for saving data under invalid scenario types

    sts_ac_scenarios = {"fr": {"battery": {"c1": {"0": 2}}}}
    res = client.put(
        f"/v1/studies/{study_id}/config/scenariobuilder/shortTermStorageAdditionalConstraints",
        json={"shortTermStorageAdditionalConstraints": sts_ac_scenarios},
    )
    assert res.status_code == 422
    assert res.json()["exception"] == "ValidationError"
    assert f"Field storage_constraints is not a valid field for study version {version}" in res.json()["description"]

    # If the scenario builder is written with wrong values, the reading should also fail

    # Write data directly in the file to bypass verification
    file_path = tmp_path / "internal_workspace" / study_id / "settings" / "scenariobuilder.dat"
    file_path.write_text("""[Default Ruleset]
sts,fr,1,battery = 2
sts,fr,4,battery = 11
""")

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder")
    assert res.status_code == 422
    assert res.json()["exception"] == "InvalidFieldForVersionError"
    assert res.json()["description"] == f"Field storage_inflows is not a valid field for study version {version}"

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/shortTermStorageInflows")
    assert res.status_code == 422
    assert res.json()["exception"] == "InvalidFieldForVersionError"
    assert (
        res.json()["description"]
        == f"Invalid scenario types ['shortTermStorageInflows'] provided for version {version}"
    )
