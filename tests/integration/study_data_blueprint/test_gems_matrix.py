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

from starlette.testclient import TestClient

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.service import StudyService
from tests.study.dao.conftest import add_system_file_to_study_dao


def test_gems_matrix_nominal_case(study_service: StudyService, admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "database"}
    ).json()

    with db():
        study = study_service.get_study(study_id)
        dao = study_service.storage_service.raw_study_service.get_study_dao(study)
        add_system_file_to_study_dao(dao)

    # `electrolyser`/`p_max` is a time- and scenario-dependent parameter backed by a matrix
    res = client.get(f"/v1/studies/{study_id}/gems/electrolyser/p_max/matrix")
    assert res.status_code == 200
    assert res.json() == {
        "index": [0, 1, 2],
        "columns": [f"column_{i}" for i in range(1, 9)],
        "data": [
            [2.2, 4.4, 6.6, 8.8, 10.10, 12.12, 14.14, 16.16],
            [3.3, 6.6, 9.9, 12.12, 15.15, 18.18, 21.21, 24.24],
            [4.4, 8.8, 12.12, 16.16, 20.20, 24.24, 28.28, 32.32],
        ],
    }

    # `dsr`/`max_load` is a time-dependent, non-scenario-dependent parameter with a single column
    res = client.get(f"/v1/studies/{study_id}/gems/dsr/max_load/matrix")
    assert res.status_code == 200
    assert res.json() == {
        "index": [0, 1, 2, 3, 4, 5],
        "columns": ["column_1"],
        "data": [[10.122], [12.344], [14.0], [16.566], [18.788], [20.5]],
    }

    ##########################
    # Error cases
    ##########################

    # Unknown component
    res = client.get(f"/v1/studies/{study_id}/gems/unknown_component/p_max/matrix")
    assert res.status_code == 404
    assert res.json() == {
        "description": "Parameter 'p_max' not found for component 'unknown_component'",
        "exception": "GemsParameterNotFound",
    }

    # Unknown parameter for an existing component
    res = client.get(f"/v1/studies/{study_id}/gems/electrolyser/unknown_parameter/matrix")
    assert res.status_code == 404
    assert res.json() == {
        "description": "Parameter 'unknown_parameter' not found for component 'electrolyser'",
        "exception": "GemsParameterNotFound",
    }

    # The parameter exists but is a constant value, not a matrix
    res = client.get(f"/v1/studies/{study_id}/gems/electrolyser/efficiency/matrix")
    assert res.status_code == 400
    assert res.json() == {
        "description": "Parameter 'efficiency' had this constant value: 0.7 but should be time and/or scenario dependent",
        "exception": "GemsParameterValueIsConstantButShouldNotBe",
    }


def test_gems_matrix_unavailable_for_filesystem_studies(admin_client: TestClient) -> None:
    client = admin_client
    study_id = client.post(
        "/v1/studies", params={"name": "test_study", "version": "10.2", "storage_mode": "filesystem"}
    ).json()

    res = client.get(f"/v1/studies/{study_id}/gems/electrolyser/p_max/matrix")
    assert res.status_code == 405
    assert res.json() == {
        "description": f"Gems is unavailable for FileSystem studies, but study {study_id} tried to use it.",
        "exception": "GemsUnavailableForFileSystemStudies",
    }
