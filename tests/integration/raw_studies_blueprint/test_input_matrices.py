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


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
def test_input_matrices(client: TestClient, user_access_token: str, storage_mode: str):
    """
    Test matrices import and reading for both storage modes
    """
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a study with the right storage mode
    study_id = client.post(f"/v1/studies?name=MyStudy&storage_mode={storage_mode}").json()

    # Add an area to test the load matrix
    area_id = "my_area"
    res = client.post(f"/v1/studies/{study_id}/areas", json={"name": area_id})
    res.raise_for_status()

    # Fetch the default matrix
    load_path = f"input/load/series/load_{area_id}"
    res = client.get(f"/v1/studies/{study_id}/raw?path={load_path}")
    res.raise_for_status()
    data = res.json()["data"]
    assert data == 8760 * [[0]]

    # Try to upload a new matrix
    res = client.put(
        f"/v1/studies/{study_id}/raw?path={load_path}", files={"file": b"1\t1\t0\t1\t1\t1\n1\t1\t0\t1\t1\t1\n"}
    )
    res.raise_for_status()

    # Check the uploaded matrix
    res = client.get(f"/v1/studies/{study_id}/raw?path={load_path}")
    res.raise_for_status()
    data = res.json()["data"]
    print(data)
