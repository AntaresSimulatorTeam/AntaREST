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
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.service import StudyService

LIBRARY_ID = "andromede-v1-models-weo-hybrid"


@pytest.mark.parametrize("variant", [False, True])
def test_get_gems_model_properties(variant: bool, study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "database"}
    ).json()
    if variant:
        study_id = client.post(f"/v1/studies/{study_id}/variants", params={"name": "variant_study"}).json()

    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study = study_service.check_study_access(study_id, StudyPermissionType.WRITE)
        # The GEMS library has no dedicated write path through `StudyInterface` yet (no variant command
        # exists for it), so the full (writable) DAO is fetched directly, as `add_commands` would.
        dao = study_service.storage_service.get_storage(study).get_study_dao(study)
        dao.save_library(
            GemsLibrary.model_validate(
                {
                    "id": LIBRARY_ID,
                    "models": [
                        {
                            "id": "dsr_with_properties",
                            "properties": [{"id": "prop1"}, {"id": "prop2"}],
                        },
                        {"id": "dsr_without_properties"},
                    ],
                }
            )
        )

    res = client.get(f"/v1/studies/{study_id}/gems/{LIBRARY_ID}/dsr_with_properties/properties")
    assert res.status_code == 200
    assert res.json() == [{"name": "prop1"}, {"name": "prop2"}]

    # A model without properties returns an empty list
    res = client.get(f"/v1/studies/{study_id}/gems/{LIBRARY_ID}/dsr_without_properties/properties")
    assert res.status_code == 200
    assert res.json() == []

    # An unknown model returns a 404
    res = client.get(f"/v1/studies/{study_id}/gems/{LIBRARY_ID}/unknown_model/properties")
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Model 'unknown_model' not found in library '{LIBRARY_ID}' for study '{study_id}'",
        "exception": "GemsModelNotFound",
    }

    # An unknown library returns a 404
    res = client.get(f"/v1/studies/{study_id}/gems/unknown_library/dsr_with_properties/properties")
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Library 'unknown_library' not found for study '{study_id}'",
        "exception": "GemsLibraryNotFound",
    }


def test_get_gems_model_properties_no_library(study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "database"}
    ).json()

    # No library has been saved for the study yet
    res = client.get(f"/v1/studies/{study_id}/gems/{LIBRARY_ID}/dsr/properties")
    assert res.status_code == 404
    assert res.json() == {
        "description": f"Library '{LIBRARY_ID}' not found for study '{study_id}'",
        "exception": "GemsLibraryNotFound",
    }


def test_get_gems_model_properties_on_filesystem_study(study_service: StudyService, admin_client: TestClient) -> None:
    """
    Unlike GEMS systems/components (DB-only), GEMS libraries are also supported for filesystem
    studies, reading/writing a `library.yml` file under `input/model-libraries`.
    """
    client = admin_client
    # `storage_mode` is omitted on purpose: it defaults to the filesystem storage mode
    study_id = client.post("/v1/studies", params={"name": "test_study", "version": "10.2"}).json()

    with db(), current_user_context(DEFAULT_ADMIN_USER):
        study = study_service.check_study_access(study_id, StudyPermissionType.WRITE)
        dao = study_service.storage_service.get_storage(study).get_study_dao(study)
        dao.save_library(
            GemsLibrary.model_validate({"id": LIBRARY_ID, "models": [{"id": "dsr", "properties": [{"id": "prop1"}]}]})
        )

    res = client.get(f"/v1/studies/{study_id}/gems/{LIBRARY_ID}/dsr/properties")
    assert res.status_code == 200
    assert res.json() == [{"name": "prop1"}]
