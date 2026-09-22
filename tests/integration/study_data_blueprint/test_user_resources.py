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
    assert res.json() == {"directories": [], "files": []}

    # Create a folder
    params = {"path": "my/folder", "resource_type": "folder"}
    res = client.put(f"/v1/studies/{study_id}/user-resources", params=params)
    assert res.status_code == 200

    # Fetch all resources. Should contain the folder
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    expected_structure = {
        "directories": [
            {
                "name": "my",
                "files": [],
                "directories": [
                    {
                        "name": "folder",
                        "files": [],
                        "directories": [],
                    }
                ],
            }
        ],
        "files": [],
    }
    assert res.json() == expected_structure
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
    assert res.json() == {
        "directories": [
            {
                "name": "my",
                "files": ["file"],
                "directories": [
                    {
                        "name": "folder",
                        "files": [],
                        "directories": [],
                    }
                ],
            }
        ],
        "files": [],
    }

    # Fetch the content of the created file
    res = client.get(f"/v1/studies/{study_id}/user-resources/content?path=my/file")
    assert res.status_code == 200
    assert res.content == content

    # Delete the file
    res = client.delete(f"/v1/studies/{study_id}/user-resources?path=my/file")
    assert res.status_code == 200

    # Fetch all resources. Should contain the folder only
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == expected_structure

    # Create a folder "my". Should be a no-op as it already exists.
    res = client.put(f"/v1/studies/{study_id}/user-resources", params={"path": "my", "resource_type": "folder"})
    assert res.status_code == 200
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == expected_structure

    # Delete the folder
    res = client.delete(f"/v1/studies/{study_id}/user-resources?path=my/folder")
    assert res.status_code == 200

    # Fetch all resources. Should still contain the parent folder "my"
    res = client.get(f"/v1/studies/{study_id}/user-resources")
    assert res.status_code == 200
    assert res.json() == {"directories": [{"name": "my", "files": [], "directories": []}], "files": []}

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
    assert res.status_code == 404
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

    # Recreate a folder to be able to ask for its content
    res = client.put(f"/v1/studies/{study_id}/user-resources", params={"path": "my/folder", "resource_type": "folder"})
    assert res.status_code == 200

    # Ask for the content of a folder
    res = client.get(f"/v1/studies/{study_id}/user-resources/content?path=my/folder")
    assert res.status_code == 400
    assert res.json()["exception"] == "UserResourceIsAFolder"
    assert res.json()["description"] == "User resources 'my/folder' is a folder. Please provide a file."

    # Create a file with the same path as an existing folder. Should fail
    res = client.put(
        f"/v1/studies/{study_id}/user-resources",
        params={"path": "my/folder", "resource_type": "file"},
        files={"file": b"a"},
    )
    assert res.status_code == 500
    assert res.json()["exception"] == "CommandApplicationError"
