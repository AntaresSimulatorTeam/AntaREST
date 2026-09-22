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

import uuid
from http import HTTPStatus

from starlette.testclient import TestClient

MAX_BATCH_DELETE_SIZE = 100


class TestDeleteStudies:
    """
    Integration tests for the batch study deletion endpoint:

    - DELETE /v1/studies
    """

    def test_batch_delete_studies(self, client: TestClient, admin_access_token: str) -> None:
        """Batch deleting a list of studies removes them all and returns 204 No Content."""
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post("/v1/studies?name=study_a")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        study_a_id = res.json()

        res = client.post("/v1/studies?name=study_b")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        study_b_id = res.json()

        res = client.get("/v1/studies")
        assert res.status_code == HTTPStatus.OK
        study_ids_before = set(res.json().keys())
        assert study_a_id in study_ids_before
        assert study_b_id in study_ids_before

        res = client.request("DELETE", "/v1/studies", json={"studyIds": [study_a_id, study_b_id]})
        assert res.status_code == HTTPStatus.NO_CONTENT

        res = client.get(f"/v1/studies/{study_a_id}")
        assert res.status_code == HTTPStatus.NOT_FOUND

        res = client.get(f"/v1/studies/{study_b_id}")
        assert res.status_code == HTTPStatus.NOT_FOUND

    def test_batch_delete_empty_list(self, client: TestClient, admin_access_token: str) -> None:
        """Passing an empty study list must return 400 Bad Request."""
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.request("DELETE", "/v1/studies", json={"studyIds": []})
        assert res.status_code == HTTPStatus.BAD_REQUEST

    def test_batch_delete_also_deletes_variants(self, client: TestClient, admin_access_token: str) -> None:
        """Deleting a parent study with withVariants=true also removes all child variants."""
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post("/v1/studies?name=parent_study")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        parent_id = res.json()

        res = client.post(f"/v1/studies/{parent_id}/variants?name=child_variant")
        assert res.status_code == HTTPStatus.OK, res.json()
        variant_id = res.json()

        assert client.get(f"/v1/studies/{parent_id}").status_code == HTTPStatus.OK
        assert client.get(f"/v1/studies/{variant_id}").status_code == HTTPStatus.OK

        res = client.request("DELETE", "/v1/studies", json={"studyIds": [parent_id], "withVariants": True})
        assert res.status_code == HTTPStatus.NO_CONTENT

        assert client.get(f"/v1/studies/{parent_id}").status_code == HTTPStatus.NOT_FOUND
        assert client.get(f"/v1/studies/{variant_id}").status_code == HTTPStatus.NOT_FOUND

    def test_batch_delete_parent_without_variants_flag_forbidden(
        self, client: TestClient, admin_access_token: str
    ) -> None:
        """
        Attempting to delete a parent study that has variant children, without setting
        withVariants=true, must be rejected with 403 Forbidden.
        """
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        res = client.post("/v1/studies?name=parent_with_variant")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        parent_id = res.json()

        res = client.post(f"/v1/studies/{parent_id}/variants?name=protected_variant")
        assert res.status_code == HTTPStatus.OK, res.json()
        variant_id = res.json()

        res = client.request("DELETE", "/v1/studies", json={"studyIds": [parent_id]})
        assert res.status_code == HTTPStatus.FORBIDDEN

        assert client.get(f"/v1/studies/{parent_id}").status_code == HTTPStatus.OK
        assert client.get(f"/v1/studies/{variant_id}").status_code == HTTPStatus.OK

    def test_batch_delete_not_found(self, client: TestClient, admin_access_token: str) -> None:
        """Referencing a study ID that does not exist must return 404 Not Found."""
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        not_found_id = str(uuid.uuid4())
        res = client.request("DELETE", "/v1/studies", json={"studyIds": [not_found_id]})
        assert res.status_code == HTTPStatus.NOT_FOUND

    def test_batch_delete_exceeds_max_size(self, client: TestClient, admin_access_token: str) -> None:
        """
        Sending more than MAX_BATCH_DELETE_SIZE study IDs in a single request must return 400 Bad Request.
        """
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}

        oversized_ids = [str(uuid.uuid4()) for _ in range(MAX_BATCH_DELETE_SIZE + 1)]
        res = client.request("DELETE", "/v1/studies", json={"studyIds": oversized_ids})
        assert res.status_code == HTTPStatus.BAD_REQUEST
        body = res.json()
        description = body.get("description") or body.get("detail") or ""
        assert str(MAX_BATCH_DELETE_SIZE) in description

    def test_batch_delete_unauthenticated(self, client: TestClient, admin_access_token: str) -> None:
        """A request without an Authorization header must be rejected with 401 Unauthorized."""
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        res = client.post("/v1/studies?name=auth_test_study")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        study_id = res.json()

        client.headers = {}
        res = client.request("DELETE", "/v1/studies", json={"studyIds": [study_id]})
        assert res.status_code == HTTPStatus.UNAUTHORIZED

        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        assert client.get(f"/v1/studies/{study_id}").status_code == HTTPStatus.OK

    def test_user_can_delete_own_study(
        self, client: TestClient, admin_access_token: str, user_access_token: str
    ) -> None:
        """A regular user must be able to delete a managed study they own."""
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.post("/v1/studies?name=user_owned_study")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        study_id = res.json()

        res = client.request("DELETE", "/v1/studies", json={"studyIds": [study_id]})
        assert res.status_code == HTTPStatus.NO_CONTENT

        assert client.get(f"/v1/studies/{study_id}").status_code == HTTPStatus.NOT_FOUND

    def test_batch_delete_forbidden_for_other_users_study(
        self, client: TestClient, admin_access_token: str, user_access_token: str
    ) -> None:
        """
        A regular user must not be able to delete a study owned by another user.
        The study must remain intact after the rejected attempt.
        """
        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        res = client.post("/v1/studies?name=admin_study")
        assert res.status_code == HTTPStatus.CREATED, res.json()
        admin_study_id = res.json()

        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.request("DELETE", "/v1/studies", json={"studyIds": [admin_study_id]})
        assert res.status_code == HTTPStatus.FORBIDDEN

        client.headers = {"Authorization": f"Bearer {admin_access_token}"}
        assert client.get(f"/v1/studies/{admin_study_id}").status_code == HTTPStatus.OK
