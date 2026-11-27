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
from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.model import StudyPermissionType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import current_user_context
from antarest.study.business.model.gems.system import GemsComponent, GemsSystem
from antarest.study.service import StudyService
from tests.study.dao.conftest import add_library_file_to_study_dao


@pytest.mark.parametrize("variant", [False, True])
def test_get_gems_component_properties(variant: bool, study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "database"}
    ).json()
    if variant:
        study_id = client.post(f"/v1/studies/{study_id}/variants", params={"name": "variant_study"}).json()

    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study = study_service.check_study_access(study_id, StudyPermissionType.WRITE)
        # The GEMS system/components have no dedicated write path through `StudyInterface` yet (no variant
        # command exists for them), so the full (writable) DAO is fetched directly, as `add_commands` would.
        dao = study_service.storage_service.get_storage(study).get_study_dao(study)

        add_library_file_to_study_dao(dao)
        dao.save_system(GemsSystem(id="sys1", components=[]))
        dao.save_components(
            [
                GemsComponent.model_validate(
                    {
                        "id": "dsr_with_properties",
                        "model": "andromede-v1-models-weo-hybrid.dsr",
                        "properties": [
                            {"id": "prop1", "value": "value1"},
                            {"id": "prop2", "value": "value2"},
                        ],
                    }
                ),
                GemsComponent.model_validate(
                    {"id": "dsr_without_properties", "model": "andromede-v1-models-weo-hybrid.dsr"}
                ),
            ]
        )

    res = client.get(f"/v1/studies/{study_id}/gems/dsr_with_properties/properties")
    assert res.status_code == 200
    assert res.json() == [{"id": "prop1", "value": "value1"}, {"id": "prop2", "value": "value2"}]

    # A component without properties returns an empty list
    res = client.get(f"/v1/studies/{study_id}/gems/dsr_without_properties/properties")
    assert res.status_code == 200
    assert res.json() == []

    # An unknown component returns a 404
    res = client.get(f"/v1/studies/{study_id}/gems/unknown_component/properties")
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Component 'unknown_component' not found for study '{study_id}' ",
        "exception": "GemsParameterNotFound",
    }


def test_get_gems_component_properties_unavailable_for_filesystem_studies(
    study_service: StudyService, admin_client: TestClient
) -> None:
    client = admin_client
    # `storage_mode` is omitted on purpose: it defaults to the filesystem storage mode
    study_id = client.post("/v1/studies", params={"name": "test_study", "version": "10.2"}).json()

    res = client.get(f"/v1/studies/{study_id}/gems/some_component/properties")
    assert res.status_code == 405
    assert res.json() == {
        "description": f"Gems is unavailable for FileSystem studies, but study {study_id} tried to use it.",
        "exception": "GemsUnavailableForFileSystemStudies",
    }
