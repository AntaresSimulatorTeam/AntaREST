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

"""
End-to-end integration tests for the reserve-need chronicle matrix through
the `/raw` endpoint.

Notes on study version:
    The reserves feature requires study version >= 10.0 (see
    `CreateReserveDefinition._validate_version`). Version 10.0 is not present
    in `STUDY_REFERENCE_TEMPLATES`, so a filesystem study cannot be created
    from scratch at that version (no on-disk template). A database-mode study,
    however, does not rely on a template (see `DatabaseStudyDaoFactory`) and
    can therefore be created directly at version 10.0.

    As a result, the end-to-end HTTP test exercises the database backend only.
    The filesystem backend for reserve-need matrices is covered by the DAO-level
    tests in `tests/study/dao/` (the `dao_10_0` fixture forces the v10.0 config
    version on top of a v9.3 template).
"""

import numpy as np
from starlette.testclient import TestClient

from tests.integration.prepare_proxy import PreparerProxy


class TestReserveNeedMatrix:
    """End-to-end HTTP tests for the reserve-need matrix `/raw` endpoint."""

    def test_crud_on_reserve_need_matrix_via_raw(self, client: TestClient, user_access_token: str) -> None:
        preparer = PreparerProxy(client, user_access_token)

        # Create a v10.0 study in DATABASE storage mode.
        # (See module docstring for the rationale on why we only test database mode here.)
        study_id = preparer.create_study("reserve-need-test", version=1000, storage_mode="database")

        # Create an area.
        preparer.create_area(study_id, name="paris")

        # Create a reserve definition. The POST returns the full ReserveDefinition payload,
        # including the auto-assigned id (derived from the name, lowercased).
        res = client.post(
            f"/v1/studies/{study_id}/areas/paris/reserves",
            json={"name": "R1", "type": "up"},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        reserve = res.json()
        reserve_id = reserve["id"]
        assert reserve_id == "r1"
        assert reserve["name"] == "R1"
        assert reserve["type"] == "up"

        matrix_path = f"input/reserves/paris/{reserve_id}"

        # GET the auto-created default need matrix via /raw.
        # The default should be a 8760x1 zero matrix.
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body = res.json()
        assert "data" in body
        assert "index" in body
        assert "columns" in body
        data = np.asarray(body["data"], dtype=float)
        assert data.shape == (8760, 1)
        assert data.sum() == 0.0

        # POST a custom matrix via the /raw endpoint (JSON body). For DB-mode
        # studies `edit_study` builds a `ReplaceMatrix` command whose validator
        # accepts a `list[list[float]]` and rejects raw bytes — so we can't use
        # the multipart PUT path here. The POST endpoint is the typed equivalent.
        custom_values = [[i * 0.1] for i in range(8760)]
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
            json=custom_values,
        )
        assert res.status_code == 200, res.json()

        # GET again: the matrix content should now match what we uploaded.
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 200, res.json()
        body = res.json()
        data = np.asarray(body["data"], dtype=float)
        assert data.shape == (8760, 1)
        np.testing.assert_allclose(data, np.asarray(custom_values))

        # DELETE the reserve definition. The DELETE endpoint expects the list of
        # reserve ids as a JSON body (Sequence[SanitizedStr]).
        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/areas/paris/reserves",
            json=[reserve_id],
            headers=preparer.headers,
        )
        assert res.status_code == 204, res.text

        # GET the need matrix again: the reserve no longer exists, so the
        # database DAO raises `ReserveDefinitionNotFound` (404 Not Found).
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path},
            headers=preparer.headers,
        )
        assert res.status_code == 404, res.json()
