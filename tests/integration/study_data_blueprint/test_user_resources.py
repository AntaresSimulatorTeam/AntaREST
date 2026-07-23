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

from antarest.study.model import StorageMode


@pytest.mark.parametrize("storage_mode", [StorageMode.DATABASE, StorageMode.FILESYSTEM])
def test_nominal_case(client: TestClient, user_access_token: str, storage_mode: StorageMode) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a study with the given storage mode
    res = client.post(f"/v1/studies?name=MyStudy&storage_mode={storage_mode}")
    study_id = res.json()

    # Fetches all user resources. Should be empty
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == []

    # Create a folder
    params = {"path": "my/folder", "resource_type": "folder"}
    res = client.put(f"/v1/studies/{study_id}/user-resources", params=params)
    assert res.status_code == 200

    # Fetch all resources. Should contain the folder
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == ["my/folder"]

    # Create a file with a specific content
    content = b"specific content"
    res = client.put(
        f"/v1/studies/{study_id}/user-resources",
        params={"path": "my/file", "resource_type": "file"},
        files={"file": content},
    )
    assert res.status_code == 200

    # Fetch all resources. Should contain the file
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == ["my/file", "my/folder"]

    # Fetch the content of the created file
    res = client.get(f"/v1/studies/{study_id}/user-resources/content?path=my/file")
    assert res.status_code == 200
    assert res.content == content

    # todo: delete a file and delete a folder

    ##########################
    # Error cases
    ##########################

    # Fetches a fake user resource content. Should fail
    res = client.get(f"/v1/studies/{study_id}/user-resources/content?path=fake/path/to/file")
    assert res.status_code == 404
    assert res.json()["exception"] == "UserResourceNotFound"
    assert res.json()["description"] == "User resources not found: 'fake/path/to/file'"

    # Deletes a fake user resource. Should fail
    res = client.delete(f"/v1/studies/{study_id}/user-resources?path=fake/path/to/file")
    description = res.json()["description"]
    assert (
        "User resources not found: 'fake/path/to/file'" in description
        or "Resource deletion failed because the given path doesn't exist : fake/path/to/file" in description
    )

    # Create a folder while giving a content. Should fail
    params = {"path": "my/folder", "resource_type": "folder"}
    res = client.put(f"/v1/studies/{study_id}/user-resources", params=params, files={"file": b"any"})
    assert res.status_code == 422
    assert res.json()["exception"] == "ValidationError"
    assert "You cannot provide a blob_id for a folder" in res.json()["description"]

    # Ask for the content of a folder
    res = client.get(f"/v1/studies/{study_id}/user-resources/content?path=my/folder")
    assert res.status_code == 400
    assert res.json()["exception"] == "UserResourceIsAFolder"
    assert res.json()["description"] == "User resources 'my/folder' is a folder. Please provide a file."
