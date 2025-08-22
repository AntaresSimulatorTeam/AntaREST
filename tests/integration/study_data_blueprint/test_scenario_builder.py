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
from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import StudyPermissionType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import current_user_context
from antarest.study.business.model.area_model import AreaCreationDTO, AreaType
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.scenario_builder_model import AreaItemsScenarios, AreaScenarios
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.service import StudyService


def _initialize_study(study_service: StudyService, study_id: str):
    study_service.create_area(study_id, AreaCreationDTO(name="fr", type=AreaType.AREA))
    study_service.create_area(study_id, AreaCreationDTO(name="be", type=AreaType.AREA))
    study_service.create_link(study_id, Link(area1="be", area2="fr"))
    study = study_service.check_study_access(study_id, StudyPermissionType.WRITE)
    study_interface = study_service.get_study_interface(study)
    study_service.thermal_manager.create_cluster(
        study_interface, "fr", ThermalClusterCreation(name="Nuclear", unit_count=10, nominal_capacity=1000)
    )


def create_raw_study(study_service: StudyService) -> str:
    """
    Creates a study with:
     - 2 areas be and fr
     - one link between them
     - one thermal cluster in fr, named Nuclear

     Returns its id.
    """

    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study_id = study_service.create_study(study_name="test", version=STUDY_VERSION_9_3, group_ids=[])
        _initialize_study(study_service, study_id)
        return study_id


def create_variant_study(study_service: StudyService) -> str:
    """
    Creates a study with:
     - 2 areas be and fr
     - one link between them
     - one thermal cluster in fr, named Nuclear

     Returns its id.
    """
    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study_id = study_service.create_study(study_name="test", version=STUDY_VERSION_9_3, group_ids=[])
        _initialize_study(study_service, study_id)
        variant_service = study_service.storage_service.variant_study_service
        variant_study = variant_service.create_variant_study(study_id, name="variant")
        return variant_study.id


@pytest.mark.parametrize("variant", [False, True])
def test_scenario_builder_nominal_case(variant: bool, study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = create_variant_study(study_service) if variant else create_raw_study(study_service)

    # Load tests

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/load")
    assert res.status_code == 200
    assert res.json() == {"load": {"be": {"1": ""}, "fr": {"1": ""}}}

    scenarios: AreaScenarios = {"be": {"1": 2}}
    res = client.put(f"/v1/studies/{study_id}/config/scenariobuilder/load", json={"load": scenarios})
    assert res.status_code == 200, res.json()

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/load")
    assert res.status_code == 200
    assert res.json() == {"load": {"be": {"1": 2}, "fr": {"1": ""}}}

    # Thermal clusters tests

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/thermal")
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"1": ""}}}}

    scenarios: AreaItemsScenarios = {"be": {}, "fr": {"nuclear": {"1": 2}}}
    res = client.put(f"/v1/studies/{study_id}/config/scenariobuilder/thermal", json={"thermal": scenarios})
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"1": 2}}}}

    res = client.get(f"/v1/studies/{study_id}/config/scenariobuilder/thermal")
    assert res.status_code == 200
    assert res.json() == {"thermal": {"be": {}, "fr": {"nuclear": {"1": 2}}}}
