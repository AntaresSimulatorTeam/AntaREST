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

_OUTPUT_IDS = [
    "20201014-1425eco-goodbye",
    "20201014-1427eco",
    "20241807-1540eco-extra-outputs",
]


def _get_output_names(client: TestClient, study_id: str) -> set[str]:
    res = client.get(f"/v1/studies/{study_id}/outputs")
    assert res.status_code == 200
    return {o["name"] for o in res.json()}


@pytest.fixture(params=["file", "v2"])
def storage_type(request, client: TestClient, user_access_token: str, internal_study_id: str):
    """Parametrized fixture that runs tests with both file and parquet (V2) storage.

    Returns (mode, output_name_map) where output_name_map translates original output IDs
    to their V2 names (which may differ due to timezone-dependent name reconstruction).
    """
    if request.param == "file":
        return "file", {}

    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Convert one at a time to track name changes reliably
    output_name_map: dict[str, str] = {}
    for output_id in _OUTPUT_IDS:
        names_before = _get_output_names(client, internal_study_id)
        res = client.post(
            f"/v1/studies/{internal_study_id}/output/{output_id}/_convert",
            params={"storage_type": "V2"},
        )
        assert res.status_code == 200, f"Failed to convert {output_id}: {res.text}"
        names_after = _get_output_names(client, internal_study_id)

        new_names = names_after - names_before
        if new_names:
            # Name changed during conversion
            output_name_map[output_id] = new_names.pop()
        else:
            # Name stayed the same
            output_name_map[output_id] = output_id

    return "v2", output_name_map
